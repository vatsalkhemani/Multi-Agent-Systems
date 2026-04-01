from agents import Agent
from config import MODEL
from solo_agents.researcher import user_pain_researcher
from solo_agents.trend_scout import trend_scout
from solo_agents.competitive import competitive_intel
from solo_agents.synthesizer import synthesizer
from solo_agents.strategist import strategy_architect
from solo_agents.gtm import gtm_strategist
from solo_agents.compiler import blueprint_compiler

# Single orchestrator — no Critic, no redo loops, straight through
orchestrator = Agent(
    name="Orchestrator",
    model=MODEL,
    instructions="""You are the Orchestrator running a single-pass product strategy pipeline.

YOUR TASK — execute these steps in order:

1. Call all three research agents with the problem statement:
   - User Pain Researcher
   - Trend Scout
   - Competitive Intelligence

2. Once all return, call the Research Synthesizer with ALL their outputs.

3. Call the Strategy Architect with the synthesis + research context.

4. Call the GTM Strategist with the strategy + research context.

5. Call the Blueprint Compiler with EVERYTHING — all research, synthesis, strategy, and GTM plan. Pass the FULL text, do NOT summarize or truncate.

6. Return the Blueprint Compiler's COMPLETE output as your final answer. Do NOT summarize, shorten, or add commentary. Return the full blueprint exactly as received.

RULES:
- Pass RICH context to each agent — include the full problem statement and all prior outputs.
- Do NOT skip any agent. Call all 7 in order.
- Think out loud about your decisions before calling agents.""",
    tools=[
        user_pain_researcher.as_tool(tool_name="call_user_pain_researcher", tool_description="Research user pain points and segments."),
        trend_scout.as_tool(tool_name="call_trend_scout", tool_description="Analyze trends and timing."),
        competitive_intel.as_tool(tool_name="call_competitive_intelligence", tool_description="Map competitors and market gaps."),
        synthesizer.as_tool(tool_name="call_synthesizer", tool_description="Synthesize all research into cross-referenced insights."),
        strategy_architect.as_tool(tool_name="call_strategy_architect", tool_description="Build product strategy."),
        gtm_strategist.as_tool(tool_name="call_gtm_strategist", tool_description="Build GTM plan."),
        blueprint_compiler.as_tool(tool_name="call_blueprint_compiler", tool_description="Compile everything into a Product Strategy Blueprint."),
    ],
)
