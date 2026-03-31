# Product Strategy Forge

**9 AI agents collaborating to turn a problem statement into a Product Strategy Blueprint.**

This is a truly agentic multi-agent system built with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). The agents autonomously research, synthesize, critique, and strategize — with the LLM making all routing decisions, not Python code.

## Architecture

```
                    ┌──────────────────┐
                    │  Discovery Lead   │  ← The Brain
                    │  (orchestrator)   │     Decides which agents to call
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────────┐
              │  as_tool()   │  as_tool()        │  as_tool()
              ▼              ▼                   ▼
    ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐
    │ User Pain   │ │ Trend Scout  │ │ Competitive Intel  │
    │ Researcher  │ │              │ │                    │
    └─────────────┘ └──────────────┘ └───────────────────┘
              │  as_tool()           │  as_tool()
              ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │ Strategy Architect│   │ GTM Strategist   │
    └──────────────────┘   └──────────────────┘
              │  as_tool()           │  as_tool()
              ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │   Synthesizer    │   │ Blueprint Compiler│
    └──────────────────┘   └──────────────────┘
              │  handoff (bidirectional)
              ▼
    ┌──────────────────┐
    │     Critic        │  ← Decides to approve or send back
    └──────────────────┘
```

## What Makes This Truly Agentic

| Pattern | How It's Used |
|---------|--------------|
| **Agent-as-Tool** | Discovery Lead calls 7 specialist agents as tools — deciding which to call and when |
| **Bidirectional Handoffs** | Discovery Lead ↔ Critic. The Critic evaluates and chooses to approve or send specific agents back |
| **LLM Routing** | The Discovery Lead agent *thinks* about what to do next. No Python if-statements make routing decisions |
| **Autonomous Loops** | The critique-redo loop runs autonomously inside a single `Runner.run()` call |

## The 9 Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **Discovery Lead** | Orchestrator — decides the flow, dispatches agents |
| 2 | User Pain Researcher | Pain points, user segments, jobs-to-be-done |
| 3 | Trend Scout | Industry trends, timing, "why now" |
| 4 | Competitive Intelligence | Competitors, moats, market gaps |
| 5 | Research Synthesizer | Cross-references all research, surfaces contradictions |
| 6 | **Critic** | Evaluates work quality, sends agents back for revisions |
| 7 | Strategy Architect | Product vision, strategic bets, sequencing |
| 8 | GTM Strategist | Go-to-market plan, positioning, channels |
| 9 | Blueprint Compiler | Produces the final Product Strategy Blueprint |

## Setup

```bash
# Clone
git clone <repo-url>
cd Multi-agent-systems/product-strategy-forge

# Virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install
pip install -r requirements.txt

# API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Run

**Terminal (no UI):**
```bash
python forge.py "Your problem statement here"
```

**Streamlit UI (with human-in-the-loop):**
```bash
streamlit run app.py
```

## How It Works

1. You enter a problem statement
2. **Research Phase**: Discovery Lead dispatches 3 research agents in parallel
3. **Synthesis**: Research Synthesizer cross-references all findings
4. **Critique**: Critic evaluates — can send specific agents back for revisions
5. Human reviews and approves research
6. **Strategy Phase**: Strategy Architect + GTM Strategist build the plan
7. **Strategy Critique**: Critic evaluates again
8. Human reviews and approves
9. **Blueprint Compiler** produces the final document

The critique loop is the architectural differentiator — the Critic agent autonomously decides whether research is strong enough, and if not, hands off back to the Discovery Lead with specific instructions on what to fix.

## Output

A professional **Product Strategy Blueprint** with:
- Executive Summary
- Research Foundation (pain points, trends, competitive landscape)
- Strategic Direction (vision, bets, moat, sequencing)
- Go-to-Market (beachhead, positioning, channels, launch plan)
- Risks & Open Questions
- Agent Deliberation Log (what the Critic pushed back on and what changed)

## Tech Stack

- **OpenAI Agents SDK** — Agent definitions, tools, handoffs, Runner
- **Streamlit** — Human-in-the-loop UI
- **GPT-4o** — Powers all 9 agents
