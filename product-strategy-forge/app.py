# -*- coding: utf-8 -*-
"""
Product Strategy Forge - Streamlit UI
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
    page_title="Product Strategy Forge",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Agent visual config (HTML entity icons for Windows compat) --
AGENT_CONFIG = {
    "Discovery Lead":          {"color": "#4A90D9", "icon": "&#x1f9e0;"},
    "User Pain Researcher":    {"color": "#E67E22", "icon": "&#x1f50d;"},
    "Trend Scout":             {"color": "#27AE60", "icon": "&#x1f4c8;"},
    "Competitive Intelligence":{"color": "#8E44AD", "icon": "&#x2694;"},
    "Research Synthesizer":    {"color": "#2C3E50", "icon": "&#x1f517;"},
    "Critic":                  {"color": "#E74C3C", "icon": "&#x26a0;"},
    "Strategy Architect":      {"color": "#2980B9", "icon": "&#x265f;"},
    "GTM Strategist":          {"color": "#16A085", "icon": "&#x1f680;"},
    "Blueprint Compiler":      {"color": "#F39C12", "icon": "&#x1f4c4;"},
    "System":                  {"color": "#95A5A6", "icon": "&#x2699;"},
    "Human":                   {"color": "#3498DB", "icon": "&#x1f464;"},
}

EVENT_LABELS = {
    "agent_switch": "Active",
    "tool_called": "Calling tool",
    "tool_output": "Got result",
    "handoff_requested": "Handing off",
    "handoff_occured": "Handoff complete",
    "message_output_created": "Responding",
    "phase_complete": "Phase complete",
    "start": "Forge started",
    "approval": "Approved",
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
    "transfer_to_critic": "Critic",
    "transfer_to_discovery_lead": "Discovery Lead",
}


# =====================================================================
# SHARED STATE: Thread-safe communication between bg thread and Streamlit
# =====================================================================
# We use a module-level dict keyed by Streamlit session_id.
# The bg thread writes here; the main thread copies into st.session_state.

import threading as _threading


@st.cache_resource
def _get_global_state():
    """Persistent shared state that survives Streamlit reruns."""
    return {"lock": _threading.Lock(), "sessions": {}}


_global = _get_global_state()
_lock = _global["lock"]
_shared = _global["sessions"]


def _get_sid():
    """Get a stable session identifier."""
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
        "research_result": None,
        "strategy_result": None,
        "blueprint": None,
        "human_guidance": "",
        "error": None,
        "start_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
sid = _get_sid()
_init_shared(sid)


# Sync shared state into session state on every rerun
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
        # Check if thread finished
        if data.get("result") is not None or data.get("error"):
            st.session_state["running"] = False


_sync_shared()


# =====================================================================
# Build agents
# =====================================================================
def build_agents():
    from forge_agents.researcher import user_pain_researcher
    from forge_agents.trend_scout import trend_scout
    from forge_agents.competitive import competitive_intel
    from forge_agents.synthesizer import synthesizer
    from forge_agents.strategist import strategy_architect
    from forge_agents.gtm import gtm_strategist
    from forge_agents.compiler import blueprint_compiler
    from forge_agents.critic import critic

    research_lead = Agent(
        name="Discovery Lead",
        model=MODEL,
        instructions="""You are the Discovery Lead orchestrating Phase 1: Research & Critique.

YOUR TASK:
1. Call all three research agents in parallel with the problem statement.
2. Once all return, call the Research Synthesizer with ALL their outputs.
3. Hand off to the Critic for evaluation.
4. If the Critic sends you back: re-call the specific agents with critique feedback, re-synthesize, and hand off to Critic again. Max 2 redo rounds.
5. Once the Critic approves, return the complete research + synthesis + critique exchange as your final output.

Think out loud about your decisions. Pass rich context to each agent.""",
        tools=[
            user_pain_researcher.as_tool(tool_name="call_user_pain_researcher", tool_description="Research user pain points and segments."),
            trend_scout.as_tool(tool_name="call_trend_scout", tool_description="Analyze trends and timing."),
            competitive_intel.as_tool(tool_name="call_competitive_intelligence", tool_description="Map competitors and market gaps."),
            synthesizer.as_tool(tool_name="call_synthesizer", tool_description="Synthesize all research into cross-referenced insights."),
        ],
        handoffs=[critic],
    )
    critic.handoffs = [research_lead]

    strategy_lead = Agent(
        name="Discovery Lead",
        model=MODEL,
        instructions="""You are the Discovery Lead orchestrating Phase 2: Strategy & Critique.

You have the approved research context. YOUR TASK:
1. Call the Strategy Architect with the research and synthesis.
2. Call the GTM Strategist with the strategy + research context.
3. Hand off to the Critic for strategy evaluation.
4. If the Critic sends you back: revise and re-submit. Max 1 redo round.
5. Once approved, return the complete strategy + GTM plan + critique exchange.

Think out loud. Pass rich context.""",
        tools=[
            strategy_architect.as_tool(tool_name="call_strategy_architect", tool_description="Build product strategy."),
            gtm_strategist.as_tool(tool_name="call_gtm_strategist", tool_description="Build GTM plan."),
        ],
        handoffs=[critic],
    )

    compile_lead = Agent(
        name="Discovery Lead",
        model=MODEL,
        instructions="""You are the Discovery Lead orchestrating Phase 3: Blueprint Compilation.

CRITICAL INSTRUCTIONS:
1. Call the Blueprint Compiler tool ONCE, passing the ENTIRE input you received as the tool argument — do NOT summarize, truncate, or paraphrase. Copy the full text verbatim.
2. When the compiler returns, output its COMPLETE response as your final answer — do NOT summarize, shorten, or add commentary. Return the full blueprint exactly as received.""",
        tools=[
            blueprint_compiler.as_tool(tool_name="call_blueprint_compiler", tool_description="Compile everything into a Product Strategy Blueprint."),
        ],
    )

    return research_lead, strategy_lead, compile_lead, critic


# =====================================================================
# Background runner with RunHooks (writes to _shared, NOT st.session_state)
# =====================================================================
class ForgeHooks(RunHooks):
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
            self._shared_data = _shared.get(self.session_id, {})
            if self.session_id in _shared:
                _shared[self.session_id]["agents_used"].add(target)
        _append_event(self.session_id, agent.name, "tool_called", "Calling " + target)

    async def on_tool_end(self, context, agent, tool, result):
        target = TOOL_TO_AGENT.get(tool.name, tool.name)
        out_len = len(str(result)) if result else 0
        _append_event(self.session_id, agent.name, "tool_output", target + " returned (" + str(out_len) + " chars)")

    async def on_handoff(self, context, from_agent, to_agent):
        _append_event(self.session_id, from_agent.name, "handoff_requested", "Handing off to " + to_agent.name)
        _set_active(self.session_id, to_agent.name)
        _append_event(self.session_id, to_agent.name, "handoff_occured", "Now in control")


def _run_sync_worker(session_id, agent, input_text, result_key):
    try:
        with _lock:
            _shared[session_id]["running"] = True
            _shared[session_id]["result"] = None
            _shared[session_id]["result_key"] = result_key
            _shared[session_id]["error"] = None

        hooks = ForgeHooks(session_id)
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
        _append_event(session_id, "System", "phase_complete", "Phase complete! Output ready for review.")

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
    st.title("Product Strategy Forge")
    st.caption("9 AI agents collaborating to build your product strategy")
    st.divider()

    problem = st.text_area(
        "Problem Statement", height=150,
        placeholder="Describe the problem you want to build a product strategy for...",
        disabled=st.session_state["phase"] != "idle",
    )

    if st.session_state["phase"] == "idle":
        if st.button("Start Forge", type="primary", disabled=not problem.strip(), use_container_width=True):
            # Reset shared state
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": True}

            st.session_state["phase"] = "research"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()
            st.session_state["error"] = None
            st.session_state["_problem"] = problem

            _append_event(sid, "System", "start", "Forge initiated for: " + problem[:120] + "...")

            research_lead, strategy_lead, compile_lead, critic_agent = build_agents()
            st.session_state["_strategy_lead"] = strategy_lead
            st.session_state["_compile_lead"] = compile_lead

            thread = threading.Thread(
                target=_run_sync_worker,
                args=(sid, research_lead, "Problem Statement: " + problem, "research_result"),
                daemon=True,
            )
            thread.start()
            st.rerun()

    st.divider()

    # Pipeline
    st.subheader("Pipeline")
    phases = [("Research & Critique", "research"), ("Strategy & Critique", "strategy"), ("Blueprint", "compile")]
    current = st.session_state["phase"]
    phase_order = [p[1] for p in phases]

    for label, phase_key in phases:
        if phase_key == current and st.session_state["running"]:
            st.markdown("**>> " + label + "** `running...`")
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
    st.subheader("Agent Roster")
    active = st.session_state.get("active_agent")
    used = st.session_state.get("agents_used", set())

    for a in ["Discovery Lead", "User Pain Researcher", "Trend Scout",
              "Competitive Intelligence", "Research Synthesizer", "Critic",
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
    st.caption("Built with OpenAI Agents SDK + Azure OpenAI")


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
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": False}
            for k in list(st.session_state.keys()):
                if k != "_sid":
                    del st.session_state[k]
            st.rerun()

    elif st.session_state["running"]:
        active_name = st.session_state.get("active_agent") or "Discovery Lead"
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
            elif etype in ("handoff_requested", "handoff_occured"): bc = "#8E44AD"
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
        st.caption("No activity yet. Start the forge to see agents in action.")


with col_output:
    phase = st.session_state["phase"]

    if phase == "research" and not st.session_state["running"] and st.session_state.get("research_result"):
        st.subheader("Research & Critique Complete")
        with st.expander("View Research Output", expanded=True):
            st.markdown(st.session_state["research_result"][:5000])
            if len(st.session_state["research_result"]) > 5000:
                st.caption("(showing 5000 of " + str(len(st.session_state["research_result"])) + " chars)")

        guidance = st.text_area("Add guidance for strategy phase (optional):", key="research_guidance")

        if st.button("Approve & Build Strategy >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "strategy"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["events"] = list(_shared[sid].get("events", []))
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            strategy_lead = st.session_state.get("_strategy_lead")
            if not strategy_lead:
                _, strategy_lead, _, _ = build_agents()

            context = "Problem: " + st.session_state["_problem"] + "\n\nAPPROVED RESEARCH:\n" + st.session_state["research_result"] + "\n\n"
            if guidance:
                context += "HUMAN GUIDANCE: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Research approved." + (" Guidance: " + guidance if guidance else "") + " Moving to strategy.")

            thread = threading.Thread(target=_run_sync_worker, args=(sid, strategy_lead, context, "strategy_result"), daemon=True)
            thread.start()
            st.rerun()

    elif phase == "strategy" and not st.session_state["running"] and st.session_state.get("strategy_result"):
        st.subheader("Strategy & Critique Complete")
        with st.expander("View Strategy Output", expanded=True):
            st.markdown(st.session_state["strategy_result"][:5000])
            if len(st.session_state["strategy_result"]) > 5000:
                st.caption("(showing 5000 of " + str(len(st.session_state["strategy_result"])) + " chars)")

        guidance = st.text_area("Add guidance for blueprint (optional):", key="strategy_guidance")

        if st.button("Approve & Compile Blueprint >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "compile"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            compile_lead = st.session_state.get("_compile_lead")
            if not compile_lead:
                _, _, compile_lead, _ = build_agents()

            context = ("Problem: " + st.session_state["_problem"] + "\n\nAPPROVED RESEARCH:\n" + st.session_state["research_result"]
                       + "\n\nAPPROVED STRATEGY:\n" + st.session_state["strategy_result"] + "\n\n")
            if guidance:
                context += "HUMAN GUIDANCE: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Strategy approved. Compiling blueprint.")

            thread = threading.Thread(target=_run_sync_worker, args=(sid, compile_lead, context, "blueprint"), daemon=True)
            thread.start()
            st.rerun()

    elif phase == "compile" and not st.session_state["running"] and st.session_state.get("blueprint"):
        st.session_state["phase"] = "complete"
        st.rerun()

    elif phase == "complete" and st.session_state.get("blueprint"):
        st.subheader("Product Strategy Blueprint")
        st.balloons()
        st.markdown(st.session_state["blueprint"])
        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("Download Blueprint (.md)", st.session_state["blueprint"], file_name="product_strategy_blueprint.md", mime="text/markdown", use_container_width=True)
        with col_dl2:
            if st.button("Start New Forge", use_container_width=True):
                with _lock:
                    _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": False}
                for k in list(st.session_state.keys()):
                    if k != "_sid":
                        del st.session_state[k]
                st.rerun()

    elif st.session_state["running"]:
        st.subheader("Phase: " + phase.title())
        active_name = st.session_state.get("active_agent") or "Discovery Lead"
        st.markdown("**Currently active:** **" + str(active_name) + "**\n\nWatch the activity log on the left to see agents being called, returning results, and handing off control.")

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
        st.subheader("Welcome to the Product Strategy Forge")
        st.caption("9 AI agents collaborate to turn your problem statement into a Product Strategy Blueprint.")
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Phase 1: Research**")
            st.caption("3 researchers investigate pain points, trends, and competitors in parallel. A synthesizer cross-references everything.")
        with c2:
            st.markdown("**Phase 2: Strategy**")
            st.caption("Strategy Architect builds product vision. GTM Strategist plans go-to-market. You approve between phases.")
        with c3:
            st.markdown("**Phase 3: Blueprint**")
            st.caption("Blueprint Compiler produces a professional strategy document you can download and share.")

# =====================================================================
# Auto-refresh: at the very end so both columns render first.
# Uses st.empty() + sleep to avoid the jarring full-page reload feel.
# =====================================================================
if st.session_state["running"]:
    _refresh_placeholder = st.empty()
    time.sleep(3)
    _sync_shared()
    st.rerun()
