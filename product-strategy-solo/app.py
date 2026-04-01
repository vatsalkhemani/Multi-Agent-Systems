# -*- coding: utf-8 -*-
"""
Product Strategy Solo - Streamlit UI (No Critique Baseline)
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
    page_title="Product Strategy Solo",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Agent visual config --
AGENT_CONFIG = {
    "Orchestrator":            {"color": "#4A90D9", "icon": "&#x1f9e0;"},
    "User Pain Researcher":    {"color": "#E67E22", "icon": "&#x1f50d;"},
    "Trend Scout":             {"color": "#27AE60", "icon": "&#x1f4c8;"},
    "Competitive Intelligence":{"color": "#8E44AD", "icon": "&#x2694;"},
    "Research Synthesizer":    {"color": "#2C3E50", "icon": "&#x1f517;"},
    "Strategy Architect":      {"color": "#2980B9", "icon": "&#x265f;"},
    "GTM Strategist":          {"color": "#16A085", "icon": "&#x1f680;"},
    "Blueprint Compiler":      {"color": "#F39C12", "icon": "&#x1f4c4;"},
    "System":                  {"color": "#95A5A6", "icon": "&#x2699;"},
}

EVENT_LABELS = {
    "agent_switch": "Active",
    "tool_called": "Calling",
    "tool_output": "Returned",
    "message_output_created": "Responding",
    "phase_complete": "Complete",
    "start": "Started",
    "error": "Error",
}

TOOL_TO_AGENT = {
    "call_user_pain_researcher": "User Pain Researcher",
    "call_trend_scout": "Trend Scout",
    "call_competitive_intelligence": "Competitive Intelligence",
    "call_synthesizer": "Research Synthesizer",
    "call_strategy_architect": "Strategy Architect",
    "call_gtm_strategist": "GTM Strategist",
    "call_blueprint_compiler": "Blueprint Compiler",
}


# =====================================================================
# SHARED STATE
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
        "blueprint": None,
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
    if data.get("result") is not None:
        st.session_state["blueprint"] = data["result"]
        st.session_state["running"] = False
        with _lock:
            _shared[sid]["running"] = False
    if not data.get("running") and st.session_state["running"]:
        if data.get("result") is not None or data.get("error"):
            st.session_state["running"] = False


_sync_shared()


# =====================================================================
# RunHooks
# =====================================================================
class SoloHooks(RunHooks):
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


def _run_sync_worker(session_id, agent, input_text):
    try:
        with _lock:
            _shared[session_id]["running"] = True
            _shared[session_id]["result"] = None
            _shared[session_id]["error"] = None

        hooks = SoloHooks(session_id)
        result = Runner.run_sync(
            agent,
            input=input_text,
            max_turns=MAX_TURNS,
            hooks=hooks,
        )

        with _lock:
            _shared[session_id]["result"] = result.final_output
            _shared[session_id]["active_agent"] = None
            _shared[session_id]["running"] = False
        _append_event(session_id, "System", "phase_complete", "Blueprint complete!")

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
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Sidebar
# =====================================================================
with st.sidebar:
    st.title("Product Strategy Solo")
    st.caption("Single-pass baseline — no Critic, no redo loops")
    st.divider()

    problem = st.text_area(
        "Problem Statement", height=150,
        placeholder="Describe the problem you want to build a product strategy for...",
        disabled=st.session_state["phase"] != "idle",
    )

    if st.session_state["phase"] == "idle":
        if st.button("Generate Blueprint", type="primary", disabled=not problem.strip(), use_container_width=True):
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "error": None, "running": True}

            st.session_state["phase"] = "running"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()
            st.session_state["error"] = None

            _append_event(sid, "System", "start", "Solo pipeline started: " + problem[:120] + "...")

            from solo_agents.orchestrator import orchestrator
            thread = threading.Thread(
                target=_run_sync_worker,
                args=(sid, orchestrator, "Problem Statement: " + problem),
                daemon=True,
            )
            thread.start()
            st.rerun()

    st.divider()

    # Agent roster
    st.subheader("Agent Roster")
    active = st.session_state.get("active_agent")
    used = st.session_state.get("agents_used", set())

    for a in ["Orchestrator", "User Pain Researcher", "Trend Scout",
              "Competitive Intelligence", "Research Synthesizer",
              "Strategy Architect", "GTM Strategist", "Blueprint Compiler"]:
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
    st.caption("Single-pass baseline — GPT-4o only, no critique")


# =====================================================================
# Main area
# =====================================================================
col_log, col_output = st.columns([1, 1])

with col_log:
    st.subheader("Agent Activity Log")

    if st.session_state.get("error"):
        st.error("Error: " + st.session_state["error"])
        if st.button("Reset & Try Again"):
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "error": None, "running": False}
            for k in list(st.session_state.keys()):
                if k != "_sid":
                    del st.session_state[k]
            st.rerun()

    elif st.session_state["running"]:
        active_name = st.session_state.get("active_agent") or "Orchestrator"
        n_events = len(st.session_state.get("events", []))
        n_agents = len(st.session_state.get("agents_used", set()))
        st.info("**" + str(active_name) + "** is working... | Events: " + str(n_events) + " | Agents: " + str(n_agents), icon=":material/autorenew:")

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
        st.caption("No activity yet. Start the pipeline to see agents in action.")


with col_output:
    phase = st.session_state["phase"]

    if phase == "running" and not st.session_state["running"] and st.session_state.get("blueprint"):
        st.session_state["phase"] = "complete"
        st.rerun()

    elif phase == "complete" and st.session_state.get("blueprint"):
        st.subheader("Product Strategy Blueprint (No Critique)")
        st.balloons()
        st.markdown(st.session_state["blueprint"])
        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("Download Blueprint (.md)", st.session_state["blueprint"], file_name="product_strategy_solo.md", mime="text/markdown", use_container_width=True)
        with col_dl2:
            if st.button("Start New Run", use_container_width=True):
                with _lock:
                    _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "error": None, "running": False}
                for k in list(st.session_state.keys()):
                    if k != "_sid":
                        del st.session_state[k]
                st.rerun()

    elif st.session_state["running"]:
        st.subheader("Generating Blueprint...")
        active_name = st.session_state.get("active_agent") or "Orchestrator"
        st.markdown("**Currently active:** **" + str(active_name) + "**\n\nSingle-pass pipeline — research, synthesize, strategize, compile. No critique loops.")

        n_events = len([e for e in st.session_state.get("events", []) if e["type"] != "start"])
        n_agents = len(st.session_state.get("agents_used", set()))
        c1, c2, c3 = st.columns(3)
        c1.metric("Events", n_events)
        c2.metric("Agents Used", n_agents)
        if st.session_state.get("start_time"):
            elapsed = int(time.time() - st.session_state["start_time"])
            mins, secs = divmod(elapsed, 60)
            c3.metric("Elapsed", str(mins) + "m " + str(secs) + "s")

    elif phase == "idle":
        st.subheader("Product Strategy Solo")
        st.caption("Single-pass baseline: 8 agents, no Critic, no redo loops. Compare this output against the Forge (with Gemini Critic) to see the difference critique makes.")
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**What runs:**")
            st.caption("3 researchers (parallel) -> Synthesizer -> Strategy Architect -> GTM Strategist -> Blueprint Compiler")
        with c2:
            st.markdown("**What's missing:**")
            st.caption("No Critic agent. No redo loops. No human approval gates. No cross-provider challenge. One pass, one model, one shot.")


# =====================================================================
# Auto-refresh
# =====================================================================
if st.session_state["running"]:
    _refresh_placeholder = st.empty()
    time.sleep(3)
    _sync_shared()
    st.rerun()
