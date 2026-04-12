# -*- coding: utf-8 -*-
"""
Voyage Agents - Streamlit UI
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
    page_title="Voyage Agents",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Agent visual config (HTML entity icons for Windows compat) --
AGENT_CONFIG = {
    "Trip Director":           {"color": "#2C3E50", "icon": "&#x1f9e0;"},
    "Destination Researcher":  {"color": "#27AE60", "icon": "&#x1f30d;"},
    "Experience Curator":      {"color": "#E67E22", "icon": "&#x2b50;"},
    "Logistics Planner":       {"color": "#8E44AD", "icon": "&#x1f697;"},
    "Itinerary Architect":     {"color": "#2980B9", "icon": "&#x1f4c5;"},
    "Budget Analyst":          {"color": "#16A085", "icon": "&#x1f4b0;"},
    "Trip Reviewer":           {"color": "#E74C3C", "icon": "&#x2714;"},
    "Website Builder":         {"color": "#F39C12", "icon": "&#x1f310;"},
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
    "start": "Voyage started",
    "approval": "Approved",
    "error": "Error",
}

TOOL_TO_AGENT = {
    "call_destination_researcher": "Destination Researcher",
    "call_experience_curator": "Experience Curator",
    "call_logistics_planner": "Logistics Planner",
    "call_itinerary_architect": "Itinerary Architect",
    "call_budget_analyst": "Budget Analyst",
    "call_website_builder": "Website Builder",
    "transfer_to_trip_reviewer": "Trip Reviewer",
    "transfer_to_trip_director": "Trip Director",
}


# =====================================================================
# SHARED STATE: Thread-safe communication between bg thread and Streamlit
# =====================================================================
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
        "planning_result": None,
        "review_result": None,
        "website_html": None,
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
        if data.get("result") is not None or data.get("error"):
            st.session_state["running"] = False


_sync_shared()


# =====================================================================
# Build agents
# =====================================================================
def build_agents():
    from voyage_agents.researcher import destination_researcher
    from voyage_agents.curator import experience_curator
    from voyage_agents.logistics import logistics_planner
    from voyage_agents.itinerary import itinerary_architect
    from voyage_agents.budget import budget_analyst
    from voyage_agents.reviewer import trip_reviewer
    from voyage_agents.builder import website_builder

    # Phase 1: Research — call 3 researchers in parallel, then hand to reviewer
    research_director = Agent(
        name="Trip Director",
        model=MODEL,
        instructions="""You are the Trip Director orchestrating Phase 1: Research & Review.

YOUR TASK:
1. Call all three research agents IN PARALLEL with the full trip request:
   - call_destination_researcher
   - call_experience_curator
   - call_logistics_planner
2. Once all three return, collect their outputs. Then hand off to the Trip Reviewer for evaluation.
3. The Reviewer will ALWAYS hand off back to you with feedback.
   - If the Reviewer says "SEND BACK": re-call the specific agents mentioned with the review feedback, then hand off to Reviewer again. Max 1 redo round.
   - If the Reviewer says "APPROVE" or gives a Trip Quality Score: the research is approved.
4. Once the Reviewer approves, return ALL the research as your final output. Include the COMPLETE outputs from all three agents (destination research, curated venues, logistics) plus the Reviewer's assessment. Do NOT summarize — output the full text.

IMPORTANT: After the Reviewer hands back to you with approval, you MUST output the complete research. Do NOT call any more tools. Just return the full collected research text.

Pass the FULL trip request to each agent. Think out loud about your decisions.""",
        tools=[
            destination_researcher.as_tool(tool_name="call_destination_researcher", tool_description="Research the destination. Pass the full trip request."),
            experience_curator.as_tool(tool_name="call_experience_curator", tool_description="Curate venues and experiences. Pass the full trip request."),
            logistics_planner.as_tool(tool_name="call_logistics_planner", tool_description="Plan logistics and transport. Pass the full trip request."),
        ],
        handoffs=[trip_reviewer],
    )
    trip_reviewer.handoffs = [research_director]

    # Phase 2 & 3: Individual agents called directly (no director wrapper)
    # This avoids the director summarizing/truncating data between agents
    return research_director, itinerary_architect, budget_analyst, website_builder, trip_reviewer


# =====================================================================
# Background runner with RunHooks
# =====================================================================
class VoyageHooks(RunHooks):
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

        hooks = VoyageHooks(session_id)
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


def _run_planning_worker(session_id, input_text):
    """Run itinerary architect then budget analyst sequentially."""
    try:
        with _lock:
            _shared[session_id]["running"] = True
            _shared[session_id]["result"] = None
            _shared[session_id]["result_key"] = "planning_result"
            _shared[session_id]["error"] = None

        hooks = VoyageHooks(session_id)

        # Get agents from session or rebuild
        from voyage_agents.itinerary import itinerary_architect
        from voyage_agents.budget import budget_analyst

        # Step 1: Itinerary
        _set_active(session_id, "Itinerary Architect")
        _append_event(session_id, "Trip Director", "tool_called", "Calling Itinerary Architect")
        result1 = Runner.run_sync(itinerary_architect, input=input_text, max_turns=10, hooks=hooks)
        itinerary_out = result1.final_output
        _append_event(session_id, "Trip Director", "tool_output", "Itinerary Architect returned (" + str(len(itinerary_out)) + " chars)")

        # Step 2: Budget
        budget_input = input_text + "\n\n=== ITINERARY ===\n" + itinerary_out
        _set_active(session_id, "Budget Analyst")
        _append_event(session_id, "Trip Director", "tool_called", "Calling Budget Analyst")
        result2 = Runner.run_sync(budget_analyst, input=budget_input, max_turns=10, hooks=hooks)
        budget_out = result2.final_output
        _append_event(session_id, "Trip Director", "tool_output", "Budget Analyst returned (" + str(len(budget_out)) + " chars)")

        combined = "=== ITINERARY ===\n" + itinerary_out + "\n\n=== BUDGET ===\n" + budget_out

        with _lock:
            _shared[session_id]["result"] = combined
            _shared[session_id]["result_key"] = "planning_result"
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
    .vibe-input { font-style: italic; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Sidebar
# =====================================================================
with st.sidebar:
    st.title("Voyage Agents")
    st.caption("7 AI agents collaborate to build your interactive travel guide")
    st.divider()

    is_idle = st.session_state["phase"] == "idle"

    destination = st.text_input(
        "Destination",
        placeholder="e.g., Bali, Sri Lanka, Portugal...",
        disabled=not is_idle,
    )

    col_dates, col_group = st.columns(2)
    with col_dates:
        duration = st.text_input(
            "Duration",
            placeholder="e.g., 5 days",
            disabled=not is_idle,
        )
    with col_group:
        group = st.text_input(
            "Group",
            placeholder="e.g., 6 friends",
            disabled=not is_idle,
        )

    budget = st.text_input(
        "Budget per person",
        placeholder="e.g., $800, INR 60000...",
        disabled=not is_idle,
    )

    interests = st.text_input(
        "Interests",
        placeholder="e.g., surfing, food, nightlife, culture...",
        disabled=not is_idle,
    )

    vibe = st.text_area(
        "Trip Vibe",
        height=100,
        placeholder="Describe your dream trip... e.g., 'Chill mornings with coffee and surf, long lunches at hidden cafes, golden hour at beach clubs, wild nights out on weekends. We want to feel like locals, not tourists.'",
        disabled=not is_idle,
    )

    # Build the trip request string
    trip_parts = []
    if destination:
        trip_parts.append(f"Destination: {destination}")
    if duration:
        trip_parts.append(f"Duration: {duration}")
    if group:
        trip_parts.append(f"Group: {group}")
    if budget:
        trip_parts.append(f"Budget: {budget} per person")
    if interests:
        trip_parts.append(f"Interests: {interests}")
    if vibe:
        trip_parts.append(f"Vibe: {vibe}")
    trip_request = "\n".join(trip_parts)

    has_minimum = bool(destination and destination.strip())

    if is_idle:
        if st.button("Plan My Trip", type="primary", disabled=not has_minimum, use_container_width=True):
            # Reset shared state
            with _lock:
                _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": True}

            st.session_state["phase"] = "research"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()
            st.session_state["error"] = None
            st.session_state["_trip_request"] = trip_request

            _append_event(sid, "System", "start", "Voyage initiated for: " + destination)

            research_director, itinerary_arch, budget_an, web_builder, reviewer = build_agents()
            st.session_state["_itinerary_architect"] = itinerary_arch
            st.session_state["_budget_analyst"] = budget_an
            st.session_state["_website_builder"] = web_builder

            thread = threading.Thread(
                target=_run_sync_worker,
                args=(sid, research_director, "Trip Request:\n" + trip_request, "research_result"),
                daemon=True,
            )
            thread.start()
            st.rerun()

    st.divider()

    # Pipeline
    st.subheader("Pipeline")
    phases = [
        ("Research & Review", "research"),
        ("Itinerary & Budget", "planning"),
        ("Build Website", "build"),
    ]
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

    for a in ["Trip Director", "Destination Researcher", "Experience Curator",
              "Logistics Planner", "Itinerary Architect", "Budget Analyst",
              "Trip Reviewer", "Website Builder"]:
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
        active_name = st.session_state.get("active_agent") or "Trip Director"
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
        st.caption("No activity yet. Fill in your trip details and hit 'Plan My Trip'!")


with col_output:
    phase = st.session_state["phase"]

    # ── Research complete → approve to plan ──
    if phase == "research" and not st.session_state["running"] and st.session_state.get("research_result"):
        st.subheader("Research & Review Complete")
        with st.expander("View Research Output", expanded=True):
            st.markdown(st.session_state["research_result"][:6000])
            if len(st.session_state["research_result"]) > 6000:
                st.caption("(showing 6000 of " + str(len(st.session_state["research_result"])) + " chars)")

        guidance = st.text_area("Add guidance for planning phase (optional):", key="research_guidance")

        if st.button("Approve & Build Itinerary >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "planning"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["events"] = list(_shared[sid].get("events", []))
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            context = ("Trip Request:\n" + st.session_state["_trip_request"]
                       + "\n\nAPPROVED RESEARCH:\n" + st.session_state["research_result"] + "\n\n")
            if guidance:
                context += "HUMAN GUIDANCE: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Research approved." + (" Guidance: " + guidance if guidance else "") + " Moving to planning.")

            thread = threading.Thread(target=_run_planning_worker, args=(sid, context), daemon=True)
            thread.start()
            st.rerun()

    # ── Planning complete → approve to build ──
    elif phase == "planning" and not st.session_state["running"] and st.session_state.get("planning_result"):
        st.subheader("Itinerary & Budget Complete")
        with st.expander("View Plan", expanded=True):
            st.markdown(st.session_state["planning_result"][:6000])
            if len(st.session_state["planning_result"]) > 6000:
                st.caption("(showing 6000 of " + str(len(st.session_state["planning_result"])) + " chars)")

        guidance = st.text_area("Add guidance for website build (optional):", key="planning_guidance")

        if st.button("Approve & Build Website >>", type="primary", use_container_width=True):
            st.session_state["phase"] = "build"
            st.session_state["running"] = True
            st.session_state["start_time"] = time.time()

            with _lock:
                _shared[sid]["result"] = None
                _shared[sid]["result_key"] = None
                _shared[sid]["error"] = None
                _shared[sid]["running"] = True

            web_builder = st.session_state.get("_website_builder")
            if not web_builder:
                _, _, _, web_builder, _ = build_agents()

            context = ("Trip Request:\n" + st.session_state["_trip_request"]
                       + "\n\nAPPROVED RESEARCH:\n" + st.session_state["research_result"]
                       + "\n\nAPPROVED ITINERARY & BUDGET:\n" + st.session_state["planning_result"] + "\n\n")
            if guidance:
                context += "HUMAN GUIDANCE: " + guidance + "\n"

            _append_event(sid, "Human", "approval", "Plan approved. Building website.")

            thread = threading.Thread(target=_run_sync_worker, args=(sid, web_builder, context, "website_html"), daemon=True)
            thread.start()
            st.rerun()

    # ── Build complete → show result ──
    elif phase == "build" and not st.session_state["running"] and st.session_state.get("website_html"):
        st.session_state["phase"] = "complete"
        st.rerun()

    elif phase == "complete" and st.session_state.get("website_html"):
        st.subheader("Your Travel Guide is Ready!")
        st.balloons()

        json_output = st.session_state["website_html"]

        # Build HTML from JSON + template
        import re as _re
        import json as _json
        from voyage_agents.template import HTML_TEMPLATE

        json_str = _re.sub(r'^```\w*\n', '', json_output.strip())
        json_str = _re.sub(r'\n```\s*$', '', json_str.strip())
        match = _re.search(r'(\{.*\})', json_str, _re.DOTALL)
        if match:
            json_str = match.group(1)
        try:
            data = _json.loads(json_str)
            clean_json = _json.dumps(data, ensure_ascii=False)
            title = data.get("destination", "Trip") + " Travel Guide"
            primary = data.get("primary_color", "#7DB8D4")
            primary_light = data.get("primary_light", "#A8D8EA")
        except _json.JSONDecodeError:
            clean_json = json_str
            title = "Travel Guide"
            primary = "#7DB8D4"
            primary_light = "#A8D8EA"

        html_content = HTML_TEMPLATE.replace("{{TRIP_DATA}}", clean_json)
        html_content = html_content.replace("{{TITLE}}", title)
        html_content = html_content.replace("{{PRIMARY_COLOR}}", primary)
        html_content = html_content.replace("{{PRIMARY_LIGHT}}", primary_light)

        st.components.v1.html(html_content, height=700, scrolling=True)

        st.divider()
        dest_name = st.session_state.get("_trip_request", "trip").split("\n")[0].replace("Destination: ", "").strip()
        safe_name = dest_name.lower().replace(" ", "_").replace(",", "")
        filename = f"voyage_{safe_name}_guide.html"

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "Download Travel Guide (.html)",
                html_content,
                file_name=filename,
                mime="text/html",
                use_container_width=True,
            )
        with col_dl2:
            if st.button("Plan Another Trip", use_container_width=True):
                with _lock:
                    _shared[sid] = {"events": [], "active_agent": None, "agents_used": set(), "result": None, "result_key": None, "error": None, "running": False}
                for k in list(st.session_state.keys()):
                    if k != "_sid":
                        del st.session_state[k]
                st.rerun()

    # ── Running state ──
    elif st.session_state["running"]:
        st.subheader("Phase: " + phase.replace("_", " ").title())
        active_name = st.session_state.get("active_agent") or "Trip Director"
        st.markdown("**Currently active:** **" + str(active_name) + "**\n\nWatch the activity log on the left to see agents researching, planning, and building your travel guide.")

        n_events = len([e for e in st.session_state.get("events", []) if e["type"] != "start"])
        n_agents = len(st.session_state.get("agents_used", set()))
        c1, c2, c3 = st.columns(3)
        c1.metric("Events", n_events)
        c2.metric("Agents Used", n_agents)
        if st.session_state.get("start_time"):
            elapsed = int(time.time() - st.session_state["start_time"])
            mins, secs = divmod(elapsed, 60)
            c3.metric("Elapsed", str(mins) + "m " + str(secs) + "s")

    # ── Idle state ──
    elif phase == "idle":
        st.subheader("Welcome to Voyage Agents")
        st.caption("7 AI agents collaborate to research, plan, review, and build your interactive travel guide.")
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Phase 1: Research**")
            st.caption("3 researchers investigate the destination, curate experiences, and plan logistics in parallel. A reviewer quality-checks everything.")
        with c2:
            st.markdown("**Phase 2: Plan**")
            st.caption("Itinerary Architect builds a day-by-day schedule. Budget Analyst prices everything and finds savings.")
        with c3:
            st.markdown("**Phase 3: Build**")
            st.caption("Website Builder assembles a beautiful, interactive HTML travel guide with maps, venues, and budget — ready to share.")

        st.divider()
        st.markdown("**How it works:**")
        st.markdown("""
1. Fill in your trip details in the sidebar — destination, duration, group, budget
2. Describe your **vibe** — this shapes everything from venues to pacing
3. Hit **Plan My Trip** and watch 7 agents collaborate in real time
4. Approve between phases with optional guidance
5. Download your interactive travel guide and share it with friends
""")


# =====================================================================
# Auto-refresh while running
# =====================================================================
if st.session_state["running"]:
    _refresh_placeholder = st.empty()
    time.sleep(3)
    _sync_shared()
    st.rerun()
