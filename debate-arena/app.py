# -*- coding: utf-8 -*-
"""
Debate Arena - Streamlit UI
Run: streamlit run app.py
"""

import sys
import os
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from agents import Agent, Runner, RunHooks, RunConfig

from config import MODEL, MAX_TURNS

# -- Page config --
st.set_page_config(
    page_title="Debate Arena",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Agent visual config --
AGENT_CONFIG = {
    "Moderator":        {"color": "#4A90D9", "icon": "&#x2696;"},
    "Advocate Alpha":   {"color": "#E74C3C", "icon": "&#x1f525;"},
    "Advocate Beta":    {"color": "#2980B9", "icon": "&#x1f4a7;"},
    "Devil's Advocate": {"color": "#8E44AD", "icon": "&#x1f608;"},
    "Judge":            {"color": "#F39C12", "icon": "&#x2696;"},
    "Synthesizer":      {"color": "#27AE60", "icon": "&#x1f4d1;"},
    "System":           {"color": "#95A5A6", "icon": "&#x2699;"},
    "Human":            {"color": "#3498DB", "icon": "&#x1f464;"},
}

EVENT_LABELS = {
    "agent_switch": "Active",
    "tool_called": "Calling",
    "tool_output": "Returned",
    "message_output_created": "Responding",
    "phase_complete": "Phase complete",
    "start": "Debate started",
    "approval": "Approved",
    "error": "Error",
}

TOOL_TO_AGENT = {
    "call_advocate_alpha": "Advocate Alpha",
    "call_advocate_beta": "Advocate Beta",
    "call_devils_advocate": "Devil's Advocate",
    "call_judge": "Judge",
    "call_synthesizer": "Synthesizer",
}


# =====================================================================
# SHARED STATE: Thread-safe communication between bg thread and Streamlit
# =====================================================================
import threading as _threading


@st.cache_resource
def _get_global_state():
    return {"lock": _threading.Lock(), "sessions": {}}


_global = _get_global_state()
_lock = _global["lock"]
_shared = _global["sessions"]


def _get_sid():
    if "_sid" not in st.session_state:
        import uuid
        st.session_state["_sid"] = str(uuid.uuid4())
    return st.session_state["_sid"]


def _init_shared(sid):
    with _lock:
        if sid not in _shared:
            _shared[sid] = {
                "events": [],
                "active_agent": None,
                "agents_used": set(),
                "result": None,
                "result_key": None,
                "error": None,
                "running": False,
            }


def _get_shared(sid):
    with _lock:
        return dict(_shared.get(sid, {}))


def _append_event(sid, agent, etype, content):
    with _lock:
        if sid in _shared:
            _shared[sid]["events"].append({
                "agent": agent,
                "type": etype,
                "content": content,
                "time": datetime.now().strftime("%H:%M:%S"),
            })


def _set_active(sid, agent_name):
    with _lock:
        if sid in _shared:
            _shared[sid]["active_agent"] = agent_name
            _shared[sid]["agents_used"].add(agent_name)


# =====================================================================
# Session state init
# =====================================================================
def init_state():
    defaults = {
        "phase": "idle",
        "running": False,
        "events": [],
        "active_agent": None,
        "agents_used": set(),
        "opening_result": None,
        "debate_result": None,
        "brief": None,
        "error": None,
        "start_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
sid = _get_sid()
_init_shared(sid)


def _sync_shared():
    data = _get_shared(sid)
    if not data:
        return
    st.session_state["events"] = list(data.get("events", []))
    st.session_state["active_agent"] = data.get("active_agent")
    st.session_state["agents_used"] = set(data.get("agents_used", set()))
    if data.get("error"):
        st.session_state["error"] = data["error"]
        st.session_state["running"] = False
    if data.get("result") is not None and data.get("result_key"):
        st.session_state[data["result_key"]] = data["result"]
        st.session_state["running"] = False
        with _lock:
            _shared[sid]["running"] = False
    if not data.get("running") and st.session_state["running"]:
        if data.get("result") is not None or data.get("error"):
            st.session_state["running"] = False


_sync_shared()


# =====================================================================
# Build agents
# =====================================================================
def build_agents():
    from arena_agents.moderator import opening_moderator, debate_moderator, verdict_moderator
    return opening_moderator, debate_moderator, verdict_moderator


# =====================================================================
# RunHooks
# =====================================================================
class ArenaHooks(RunHooks):
    def __init__(self, session_id):
        self.session_id = session_id

    async def on_agent_start(self, context, agent):
        _set_active(self.session_id, agent.name)
        _append_event(self.session_id, agent.name, "agent_switch", "Agent now active")

    async def on_agent_end(self, context, agent, output):
        _append_event(self.session_id, agent.name, "message_output_created", "Finished response")

    async def on_tool_start(self, context, agent, tool):
        target = TOOL_TO_AGENT.get(tool.name, tool.name)
        with _lock:
            if self.session_id in _shared:
                _shared[self.session_id]["agents_used"].add(target)
        _append_event(self.session_id, agent.name, "tool_called", "Calling " + target)

    async def on_tool_end(self, context, agent, tool, result):
        target = TOOL_TO_AGENT.get(tool.name, tool.name)
        out_len = len(str(result)) if result else 0
        _append_event(self.session_id, agent.name, "tool_output", target + " returned (" + str(out_len) + " chars)")


def _run_sync_worker(session_id, agent, input_text, result_key):
    try:
        with _lock:
            _shared[session_id]["running"] = True
            _shared[session_id]["result"] = None
            _shared[session_id]["result_key"] = result_key
            _shared[session_id]["error"] = None

        hooks = ArenaHooks(session_id)
        result = Runner.run_sync(
            agent,
            input=input_text,
            max_turns=MAX_TURNS,
            hooks=hooks,
        )

        with _lock:
            _shared[session_id]["result"] = result.final_output
            _shared[session_id]["result_key"] = result_key
            _shared[session_id]["active_agent"] = None
            _shared[session_id]["running"] = False
        _append_event(session_id, "System", "phase_complete", "Phase complete!")

    except Exception as e:
        with _lock:
            _shared[session_id]["error"] = str(e)
            _shared[session_id]["running"] = False
        _append_event(session_id, "System", "error", str(e)[:300])


# =====================================================================
# Custom CSS
# =====================================================================
st.markdown("""
<style>
    .agent-card {
        border-left: 4px solid;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 6px;
        background: #f8f9fa;
        font-size: 0.9em;
    }
    .agent-name { font-weight: 700; font-size: 0.95em; }
    .agent-time { color: #999; font-size: 0.75em; float: right; }
    .agent-content { margin-top: 4px; color: #444; }
    .status-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; margin-right: 6px;
    }
    .status-active { background: #27AE60; animation: pulse 1.5s infinite; }
    .status-done { background: #95A5A6; }
    .status-idle { background: #ddd; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    .round-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 700;
        color: white;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Sidebar
# =====================================================================
with st.sidebar:
    st.title("Debate Arena")
    st.caption("Multi-agent adversarial debate for better decisions")
    st.divider()

    decision = st.text_area(
        "Decision Prompt", height=150,
        placeholder="Describe the decision you need to make...\n\nExample: Should we build our own ML platform in-house or buy an existing solution?",
        disabled=st.session_state["phase"] != "idle",
    )

    if st.session_state["phase"] == "idle":
        if st.button("Start Debate", type="primary", disabled=not decision.strip(), use_container_width=True):
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": True}

            st.session_state["phase"] = "opening"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()
            st.session_state["error"] = None
            st.session_state["_decision"] = decision

            _append_event(sid, "System", "start", "Debate initiated: " + decision[:120] + "...")

            opening_mod, debate_mod, verdict_mod = build_agents()
            st.session_state["_debate_mod"] = debate_mod
            st.session_state["_verdict_mod"] = verdict_mod

            thread = threading.Thread(
                target=_run_sync_worker,
                args=(sid, opening_mod, "DECISION TO DEBATE: " + decision, "opening_result"),
                daemon=True,
            )
            thread.start()
            st.rerun()

    st.divider()

    # Round progress
    st.subheader("Debate Rounds")
    phases = [
        ("Round 1: Opening Arguments", "opening"),
        ("Round 2-3: Cross-Exam & Rebuttals", "debate"),
        ("Verdict & Decision Brief", "verdict"),
    ]
    current = st.session_state["phase"]
    phase_order = [p[1] for p in phases]

    for label, phase_key in phases:
        if phase_key == current and st.session_state["running"]:
            st.markdown("**>> " + label + "** `in progress...`")
            if st.session_state.get("start_time"):
                elapsed = int(time.time() - st.session_state["start_time"])
                mins, secs = divmod(elapsed, 60)
                st.caption("Elapsed: " + str(mins) + "m " + str(secs) + "s")
        elif phase_key == current and not st.session_state["running"]:
            st.markdown("**> " + label + "** `awaiting approval`")
        elif phase_key in phase_order and current in phase_order and phase_order.index(phase_key) < phase_order.index(current):
            st.markdown("[done] ~~" + label + "~~")
        elif current == "complete":
            st.markdown("[done] ~~" + label + "~~")
        else:
            st.markdown("[ ] " + label)

    st.divider()

    # Agent roster
    st.subheader("Debaters & Officials")
    active = st.session_state.get("active_agent")
    used = st.session_state.get("agents_used", set())

    for a in ["Moderator", "Advocate Alpha", "Advocate Beta", "Devil's Advocate", "Judge", "Synthesizer"]:
        cfg = AGENT_CONFIG.get(a, {"color": "#666", "icon": "&#x2699;"})
        if a == active:
            sc, sl = "status-active", "ACTIVE"
        elif a in used:
            sc, sl = "status-done", "done"
        else:
            sc, sl = "status-idle", "waiting"
        st.markdown(
            '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
            '<span class="status-dot ' + sc + '"></span>'
            '<span style="color:' + cfg["color"] + ';font-weight:600;">' + cfg["icon"] + ' ' + a + '</span>'
            '<span style="color:#999;font-size:0.75em;margin-left:auto;">' + sl + '</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Built with OpenAI Agents SDK + Azure OpenAI")


# =====================================================================
# Main area
# =====================================================================
col_log, col_output = st.columns([1, 1])

with col_log:
    st.subheader("Arena Activity Log")

    if st.session_state.get("error"):
        st.error("Error: " + st.session_state["error"])
        if st.button("Reset & Try Again"):
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": False}
            for k in list(st.session_state.keys()):
                if k != "_sid":
                    del st.session_state[k]
            st.rerun()

    elif st.session_state["running"]:
        active_name = st.session_state.get("active_agent") or "Moderator"
        n_events = len(st.session_state.get("events", []))
        n_agents = len(st.session_state.get("agents_used", set()))
        st.info("**" + str(active_name) + "** is working... | Events: " + str(n_events) + " | Agents: " + str(n_agents), icon=":material/autorenew:")

    # Show events (newest first)
    events = st.session_state.get("events", [])
    if events:
        for event in reversed(events):
            agent = event["agent"]
            cfg = AGENT_CONFIG.get(agent, {"color": "#666", "icon": "&#x2699;"})
            color = cfg["color"]
            icon = cfg["icon"]
            etype = event["type"]
            label = EVENT_LABELS.get(etype, etype)
            ts = event.get("time", "")
            content = event["content"]

            if etype == "error": bc = "#E74C3C"
            elif etype == "tool_called": bc = "#3498DB"
            elif etype == "tool_output": bc = "#27AE60"
            elif etype == "phase_complete": bc = "#F39C12"
            else: bc = "#95A5A6"

            st.markdown(
                '<div class="agent-card" style="border-left-color:' + color + ';">'
                '<span class="agent-time">' + ts + '</span>'
                '<span class="agent-name" style="color:' + color + ';">' + icon + ' ' + agent + '</span> '
                '<span style="background:' + bc + ';color:white;padding:1px 8px;border-radius:10px;font-size:0.7em;">' + label + '</span>'
                '<div class="agent-content">' + content + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No activity yet. Start a debate to see agents clash.")


with col_output:
    phase = st.session_state["phase"]

    # ── Phase 1 complete: show openings, ask for approval ──
    if phase == "opening" and not st.session_state["running"] and st.session_state.get("opening_result"):
        st.subheader("Round 1: Opening Arguments Complete")
        with st.expander("View Opening Arguments", expanded=True):
            st.markdown(st.session_state["opening_result"][:8000])
            if len(st.session_state["opening_result"]) > 8000:
                st.caption("(showing 8000 of " + str(len(st.session_state["opening_result"])) + " chars)")

        guidance = st.text_area("Add guidance for the debate rounds (optional):", key="opening_guidance",
                                placeholder="e.g., 'Focus more on cost implications' or 'Challenge the timeline assumptions'")

        if st.button("Approve & Start Cross-Examination >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "debate"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["events"] = list(_shared[sid].get("events", []))
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            debate_mod = st.session_state.get("_debate_mod")
            if not debate_mod:
                _, debate_mod, _ = build_agents()

            context = "DECISION: " + st.session_state["_decision"] + "\n\nPHASE 1 TRANSCRIPT (Opening Arguments):\n" + st.session_state["opening_result"] + "\n\n"
            if guidance:
                context += "HUMAN GUIDANCE FOR DEBATE: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Openings approved." + (" Guidance: " + guidance if guidance else "") + " Starting cross-examination.")

            thread = threading.Thread(target=_run_sync_worker, args=(sid, debate_mod, context, "debate_result"), daemon=True)
            thread.start()
            st.rerun()

    # ── Phase 2 complete: show debate, ask for approval ──
    elif phase == "debate" and not st.session_state["running"] and st.session_state.get("debate_result"):
        st.subheader("Rounds 2-3: Cross-Examination & Rebuttals Complete")
        with st.expander("View Debate Transcript", expanded=True):
            st.markdown(st.session_state["debate_result"][:8000])
            if len(st.session_state["debate_result"]) > 8000:
                st.caption("(showing 8000 of " + str(len(st.session_state["debate_result"])) + " chars)")

        guidance = st.text_area("Add guidance for the verdict (optional):", key="debate_guidance",
                                placeholder="e.g., 'Weight risk analysis more heavily' or 'Consider hybrid approaches'")

        if st.button("Approve & Render Verdict >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "verdict"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            verdict_mod = st.session_state.get("_verdict_mod")
            if not verdict_mod:
                _, _, verdict_mod = build_agents()

            context = ("DECISION: " + st.session_state["_decision"]
                       + "\n\nPHASE 1 — OPENING ARGUMENTS:\n" + st.session_state["opening_result"]
                       + "\n\nPHASE 2 — CROSS-EXAMINATION & REBUTTALS:\n" + st.session_state["debate_result"] + "\n\n")
            if guidance:
                context += "HUMAN GUIDANCE FOR VERDICT: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Debate approved. Rendering verdict.")

            thread = threading.Thread(target=_run_sync_worker, args=(sid, verdict_mod, context, "brief"), daemon=True)
            thread.start()
            st.rerun()

    # ── Phase 3 complete: transition ──
    elif phase == "verdict" and not st.session_state["running"] and st.session_state.get("brief"):
        st.session_state["phase"] = "complete"
        st.rerun()

    # ── Complete: show brief ──
    elif phase == "complete" and st.session_state.get("brief"):
        st.subheader("Decision Brief")
        st.balloons()
        st.markdown(st.session_state["brief"])
        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("Download Brief (.md)", st.session_state["brief"], file_name="decision_brief.md", mime="text/markdown", use_container_width=True)
        with col_dl2:
            if st.button("Start New Debate", use_container_width=True):
                with _lock:
                    _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": False}
                for k in list(st.session_state.keys()):
                    if k != "_sid":
                        del st.session_state[k]
                st.rerun()

    # ── Running: show progress ──
    elif st.session_state["running"]:
        st.subheader("Phase: " + phase.replace("_", " ").title())
        active_name = st.session_state.get("active_agent") or "Moderator"
        st.markdown("**Currently active:** **" + str(active_name) + "**\n\nWatch the activity log on the left to see agents debating.")

        n_events = len([e for e in st.session_state.get("events", []) if e["type"] != "start"])
        n_agents = len(st.session_state.get("agents_used", set()))
        c1, c2, c3 = st.columns(3)
        c1.metric("Events", n_events)
        c2.metric("Agents Active", n_agents)
        if st.session_state.get("start_time"):
            elapsed = int(time.time() - st.session_state["start_time"])
            mins, secs = divmod(elapsed, 60)
            c3.metric("Elapsed", str(mins) + "m " + str(secs) + "s")

    # ── Idle: welcome ──
    elif phase == "idle":
        st.subheader("Welcome to the Debate Arena")
        st.caption("6 AI agents engage in structured adversarial debate to produce better decisions.")
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Round 1: Opening**")
            st.caption("Moderator frames 2 positions. Advocate Alpha and Beta argue their sides. Devil's Advocate challenges both.")
        with c2:
            st.markdown("**Rounds 2-3: Clash**")
            st.caption("Cross-examination: agents attack each other's arguments. Rebuttals: agents defend and strengthen. This is where quality emerges.")
        with c3:
            st.markdown("**Verdict**")
            st.caption("Judge scores all arguments. Synthesizer compiles a professional Decision Brief you can download and share.")


# =====================================================================
# Auto-refresh while running
# =====================================================================
if st.session_state["running"]:
    _refresh_placeholder = st.empty()
    time.sleep(3)
    _sync_shared()
    st.rerun()
