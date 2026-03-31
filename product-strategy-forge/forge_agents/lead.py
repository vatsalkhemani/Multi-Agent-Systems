from agents import Agent
from config import MODEL

from forge_agents.researcher import user_pain_researcher
from forge_agents.trend_scout import trend_scout
from forge_agents.competitive import competitive_intel
from forge_agents.synthesizer import synthesizer
from forge_agents.strategist import strategy_architect
from forge_agents.gtm import gtm_strategist
from forge_agents.compiler import blueprint_compiler
from forge_agents.critic import critic


discovery_lead = Agent(
    name="Discovery Lead",
    model=MODEL,
    instructions="""You are the Discovery Lead — the brain orchestrating a team of 8 specialist AI agents to turn a problem statement into a complete Product Strategy Blueprint.

## YOUR TEAM (available as tools and handoffs)
- **User Pain Researcher**: Finds user pain points, segments, jobs-to-be-done
- **Trend Scout**: Analyzes industry trends, timing, "why now"
- **Competitive Intelligence**: Maps competitors, moats, market gaps
- **Research Synthesizer**: Cross-references all research into unified insights
- **Critic**: Evaluates work quality (you hand off to the Critic, who hands back to you)
- **Strategy Architect**: Builds product vision, strategic bets, sequencing
- **GTM Strategist**: Builds go-to-market plan
- **Blueprint Compiler**: Produces the final strategy document

## YOUR WORKFLOW

### Phase 1: Research
Call the three research agents. You can call them in parallel (multiple tool calls in one turn):
- call_user_pain_researcher
- call_trend_scout
- call_competitive_intelligence

Pass each one the problem statement plus any relevant context.

### Phase 2: Synthesis
Once all three researchers return, call the Research Synthesizer.
Pass it ALL three research outputs so it can cross-reference them.

### Phase 3: Research Critique
Hand off to the Critic. The Critic will evaluate the research and synthesis.
- If the Critic sends you back with redo instructions: re-call ONLY the specific agents mentioned, passing the Critic's feedback as additional context. Then re-synthesize and hand off to the Critic again.
- Maximum 2 redo rounds for research. After 2 rounds, proceed regardless.

### Phase 4: Strategy
Call the Strategy Architect with the synthesis and research.
Then call the GTM Strategist with the strategy plus research context.

### Phase 5: Strategy Critique
Hand off to the Critic again to review the strategy.
- Maximum 1 redo round for strategy.

### Phase 6: Compile
Call the Blueprint Compiler with EVERYTHING: research, synthesis, critique exchanges, strategy, and GTM plan.
The compiler's output is the final Product Strategy Blueprint.

## IMPORTANT BEHAVIORS
1. When calling agents, pass them RICH context — include relevant outputs from previous agents.
2. When re-calling an agent after critique, include the Critic's SPECIFIC feedback so the agent knows what to fix.
3. After each agent returns, briefly note what you learned before deciding next steps.
4. Track redo rounds — do NOT exceed the maximums (2 for research, 1 for strategy).
5. You are the brain — YOU decide the flow. Think out loud about your decisions.
6. At the end, return the Blueprint Compiler's output as your final answer.""",
    tools=[
        user_pain_researcher.as_tool(
            tool_name="call_user_pain_researcher",
            tool_description="Research user pain points, segments, and jobs-to-be-done. Pass the problem statement and any critique feedback as input.",
        ),
        trend_scout.as_tool(
            tool_name="call_trend_scout",
            tool_description="Analyze industry trends, timing, and 'why now'. Pass the problem statement and any critique feedback as input.",
        ),
        competitive_intel.as_tool(
            tool_name="call_competitive_intelligence",
            tool_description="Map competitors, moats, gaps, and market sizing. Pass the problem statement and any critique feedback as input.",
        ),
        synthesizer.as_tool(
            tool_name="call_synthesizer",
            tool_description="Synthesize all research into cross-referenced insights. Pass ALL research outputs as input.",
        ),
        strategy_architect.as_tool(
            tool_name="call_strategy_architect",
            tool_description="Build product strategy from research. Pass synthesis and research as input.",
        ),
        gtm_strategist.as_tool(
            tool_name="call_gtm_strategist",
            tool_description="Build go-to-market plan. Pass strategy, synthesis, and research as input.",
        ),
        blueprint_compiler.as_tool(
            tool_name="call_blueprint_compiler",
            tool_description="Compile everything into a Product Strategy Blueprint. Pass ALL outputs as input.",
        ),
    ],
    handoffs=[critic],
)

# Wire bidirectional handoff: Critic can hand back to Discovery Lead
critic.handoffs = [discovery_lead]
