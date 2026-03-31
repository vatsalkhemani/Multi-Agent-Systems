"""
Product Strategy Forge — Streamlit UI

Run: streamlit run app.py
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from agents import Agent, Runner

from config import MODEL, MAX_TURNS

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Product Strategy Forge",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Agent colors ─────────────────────────────────────────────
AGENT_COLORS = {
    "Discovery Lead": "#4A90D9",
    "User Pain Researcher": "#E67E22",
    "Trend Scout": "#27AE60",
    "Competitive Intelligence": "#8E44AD",
    "Research Synthesizer": "#2C3E50",
    "Critic": "#E74C3C",
    "Strategy Architect": "#2980B9",
    "GTM Strategist": "#16A085",
    "Blueprint Compiler": "#7F8C8D",
}

AGENT_ICONS = {
    "Discovery Lead": "brain",
    "User Pain Researcher": "mag",
    "Trend Scout": "chart_with_upwards_trend",
    "Competitive Intelligence": "crossed_swords",
    "Research Synthesizer": "link",
    "Critic": "warning",
    "Strategy Architect": "chess_pawn",
    "GTM Strategist": "rocket",
    "Blueprint Compiler": "page_facing_up",
}


# ── Session state init ───────────────────────────────────────
def init_state():
    defaults = {
        "phase": "idle",            # idle | research | strategy | compile | complete
        "running": False,
        "events": [],               # list of {agent, type, content}
        "research_result": None,
        "strategy_result": None,
        "blueprint": None,
        "human_guidance": "",
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── Build agents fresh each run (to avoid stale refs) ────────
def build_agents():
    """Build all agents with proper wiring."""
    from forge_agents.researcher import user_pain_researcher
    from forge_agents.trend_scout import trend_scout
    from forge_agents.competitive import competitive_intel
    from forge_agents.synthesizer import synthesizer
    from forge_agents.strategist import strategy_architect
    from forge_agents.gtm import gtm_strategist
    from forge_agents.compiler import blueprint_compiler
    from forge_agents.critic import critic

    # Research phase lead
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
            user_pain_researcher.as_tool(
                tool_name="call_user_pain_researcher",
                tool_description="Research user pain points and segments. Pass problem statement + any critique feedback.",
            ),
            trend_scout.as_tool(
                tool_name="call_trend_scout",
                tool_description="Analyze trends and timing. Pass problem statement + any critique feedback.",
            ),
            competitive_intel.as_tool(
                tool_name="call_competitive_intelligence",
                tool_description="Map competitors and market gaps. Pass problem statement + any critique feedback.",
            ),
            synthesizer.as_tool(
                tool_name="call_synthesizer",
                tool_description="Synthesize all research into cross-referenced insights. Pass ALL research outputs.",
            ),
        ],
        handoffs=[critic],
    )
    critic.handoffs = [research_lead]

    # Strategy phase lead
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
            strategy_architect.as_tool(
                tool_name="call_strategy_architect",
                tool_description="Build product strategy. Pass synthesis and research context.",
            ),
            gtm_strategist.as_tool(
                tool_name="call_gtm_strategist",
                tool_description="Build GTM plan. Pass strategy + research context.",
            ),
        ],
        handoffs=[critic],
    )

    # Compile phase lead
    compile_lead = Agent(
        name="Discovery Lead",
        model=MODEL,
        instructions="""You are the Discovery Lead orchestrating Phase 3: Blueprint Compilation.

Call the Blueprint Compiler with ALL context: research, synthesis, critique exchanges, strategy, and GTM plan.
Return the compiler's output as your final answer.""",
        tools=[
            blueprint_compiler.as_tool(
                tool_name="call_blueprint_compiler",
                tool_description="Compile everything into a Product Strategy Blueprint. Pass ALL context.",
            ),
        ],
    )

    return research_lead, strategy_lead, compile_lead, critic


# ── Run a phase in background thread ─────────────────────────
def run_phase(agent, input_text, result_key):
    """Run a phase and store result in session state."""
    try:
        result = Runner.run_sync(agent, input=input_text, max_turns=MAX_TURNS)
        st.session_state[result_key] = result.final_output
        st.session_state["events"].append({
            "agent": "System",
            "type": "phase_complete",
            "content": f"Phase complete. Output ready for review.",
        })
    except Exception as e:
        st.session_state["error"] = str(e)
    finally:
        st.session_state["running"] = False


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("Product Strategy Forge")
    st.caption("9 AI agents collaborating to build your product strategy")

    st.divider()

    problem = st.text_area(
        "Problem Statement",
        height=150,
        placeholder="Describe the problem you want to build a product strategy for...",
        disabled=st.session_state["phase"] != "idle",
    )

    if st.session_state["phase"] == "idle":
        if st.button("Start Forge", type="primary", disabled=not problem.strip()):
            st.session_state["phase"] = "research"
            st.session_state["running"] = True
            st.session_state["events"] = [{
                "agent": "System",
                "type": "start",
                "content": f"Starting forge for: {problem[:100]}...",
            }]
            research_lead, strategy_lead, compile_lead, critic_agent = build_agents()
            st.session_state["_strategy_lead"] = strategy_lead
            st.session_state["_compile_lead"] = compile_lead
            st.session_state["_problem"] = problem
            thread = threading.Thread(
                target=run_phase,
                args=(research_lead, f"Problem Statement: {problem}", "research_result"),
            )
            thread.start()
            st.rerun()

    st.divider()

    # Phase progress
    st.subheader("Progress")
    phases = [
        ("Research & Critique", "research"),
        ("Strategy & Critique", "strategy"),
        ("Blueprint", "compile"),
    ]
    for label, phase_key in phases:
        current = st.session_state["phase"]
        if phase_key == current and st.session_state["running"]:
            st.markdown(f"**:hourglass_flowing_sand: {label}** _(running...)_")
        elif phase_key == current and not st.session_state["running"]:
            st.markdown(f"**:arrow_forward: {label}** _(awaiting approval)_")
        elif phases.index((label, phase_key)) < [p[1] for p in phases].index(current) if current in [p[1] for p in phases] else -1:
            st.markdown(f":white_check_mark: {label}")
        elif current == "complete":
            st.markdown(f":white_check_mark: {label}")
        else:
            st.markdown(f":white_circle: {label}")

    st.divider()
    st.caption("Built with OpenAI Agents SDK")
    st.caption("9 agents | Handoffs | Agent-as-Tool")


# ── Main area ────────────────────────────────────────────────
col_log, col_output = st.columns([1, 1])

with col_log:
    st.subheader("Agent Activity")

    if st.session_state["running"]:
        st.info("Agents are working autonomously... This may take a few minutes.", icon=":material/autorenew:")
        time.sleep(3)
        st.rerun()

    if st.session_state["error"]:
        st.error(f"Error: {st.session_state['error']}")

    # Show events
    for event in st.session_state["events"]:
        agent = event["agent"]
        color = AGENT_COLORS.get(agent, "#666")
        st.markdown(
            f'<div style="border-left: 4px solid {color}; padding: 8px 12px; margin: 4px 0; '
            f'background: #f8f9fa; border-radius: 4px;">'
            f'<strong style="color: {color};">{agent}</strong> '
            f'<span style="color: #999; font-size: 0.8em;">[{event["type"]}]</span>'
            f'<br/><span style="font-size: 0.9em;">{event["content"][:500]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


with col_output:
    phase = st.session_state["phase"]

    # ── Research phase complete → show results + approve ──
    if phase == "research" and not st.session_state["running"] and st.session_state["research_result"]:
        st.subheader("Research & Critique Complete")
        with st.expander("View Research Output", expanded=True):
            st.markdown(st.session_state["research_result"][:3000])
            if len(st.session_state["research_result"]) > 3000:
                st.caption("(truncated for display)")

        guidance = st.text_area("Add guidance for strategy phase (optional):", key="research_guidance")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Approve & Build Strategy", type="primary"):
                st.session_state["phase"] = "strategy"
                st.session_state["running"] = True
                st.session_state["human_guidance"] = guidance

                strategy_lead = st.session_state.get("_strategy_lead")
                if not strategy_lead:
                    _, strategy_lead, _, _ = build_agents()

                context = (
                    f"Problem: {st.session_state['_problem']}\n\n"
                    f"APPROVED RESEARCH:\n{st.session_state['research_result']}\n\n"
                )
                if guidance:
                    context += f"HUMAN GUIDANCE: {guidance}\n"

                st.session_state["events"].append({
                    "agent": "Human",
                    "type": "approval",
                    "content": f"Research approved.{' Guidance: ' + guidance if guidance else ''} Moving to strategy.",
                })

                thread = threading.Thread(
                    target=run_phase,
                    args=(strategy_lead, context, "strategy_result"),
                )
                thread.start()
                st.rerun()

    # ── Strategy phase complete → show results + approve ──
    elif phase == "strategy" and not st.session_state["running"] and st.session_state["strategy_result"]:
        st.subheader("Strategy & Critique Complete")
        with st.expander("View Strategy Output", expanded=True):
            st.markdown(st.session_state["strategy_result"][:3000])
            if len(st.session_state["strategy_result"]) > 3000:
                st.caption("(truncated for display)")

        guidance = st.text_area("Add guidance for blueprint (optional):", key="strategy_guidance")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Approve & Compile Blueprint", type="primary"):
                st.session_state["phase"] = "compile"
                st.session_state["running"] = True

                compile_lead = st.session_state.get("_compile_lead")
                if not compile_lead:
                    _, _, compile_lead, _ = build_agents()

                context = (
                    f"Problem: {st.session_state['_problem']}\n\n"
                    f"APPROVED RESEARCH:\n{st.session_state['research_result']}\n\n"
                    f"APPROVED STRATEGY:\n{st.session_state['strategy_result']}\n\n"
                )
                if guidance:
                    context += f"HUMAN GUIDANCE: {guidance}\n"

                st.session_state["events"].append({
                    "agent": "Human",
                    "type": "approval",
                    "content": f"Strategy approved. Compiling blueprint.",
                })

                thread = threading.Thread(
                    target=run_phase,
                    args=(compile_lead, context, "blueprint"),
                )
                thread.start()
                st.rerun()

    # ── Blueprint complete ──
    elif phase == "compile" and not st.session_state["running"] and st.session_state["blueprint"]:
        st.session_state["phase"] = "complete"
        st.rerun()

    elif phase == "complete" and st.session_state["blueprint"]:
        st.subheader("Product Strategy Blueprint")
        st.markdown(st.session_state["blueprint"])

        st.divider()
        st.download_button(
            "Download Blueprint (.md)",
            st.session_state["blueprint"],
            file_name="product_strategy_blueprint.md",
            mime="text/markdown",
        )

    # ── Running state ──
    elif st.session_state["running"]:
        st.subheader(f"Phase: {phase.title()}")
        st.info("Agents are collaborating autonomously. The Discovery Lead is coordinating research agents, synthesis, and critique...")

    # ── Idle ──
    elif phase == "idle":
        st.subheader("Welcome to the Product Strategy Forge")
        st.markdown("""
**9 AI agents** collaborate to turn your problem statement into a professional Product Strategy Blueprint.

**How it works:**
1. Enter a problem statement in the sidebar
2. **Research Phase**: 3 research agents investigate in parallel (pain points, trends, competitive landscape)
3. A **Synthesizer** cross-references findings
4. A **Critic** evaluates and can send agents back for revisions
5. You review and approve the research
6. **Strategy Phase**: Strategy Architect + GTM Strategist build the plan
7. The **Critic** evaluates again
8. You review and approve
9. **Blueprint Compiler** produces the final document

**What makes this truly agentic:**
- The Discovery Lead agent **decides** which agents to call and when
- The Critic agent **chooses** to approve or send specific agents back
- Agents hand off control to each other via the OpenAI Agents SDK
- The LLM makes routing decisions — not a Python script
        """)
