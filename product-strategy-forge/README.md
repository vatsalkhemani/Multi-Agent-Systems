# Product Strategy Forge

A multi-agent system where 9 specialized AI agents collaborate to turn a problem statement into a comprehensive Product Strategy Blueprint.

Give it a problem like *"Small businesses struggle to manage social media"* and a team of AI agents will research user pain, analyze trends, map competitors, critique each other's work, build strategy, and compile a professional strategy document.

Built with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).

## How It Works

```
                        ┌──────────────────┐
                        │  Discovery Lead   │  Orchestrator: dispatches agents,
                        │                  │  coordinates phases, responds to critique
                        └────────┬─────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
 ┌────────────────┐   ┌────────────────┐   ┌────────────────────┐
 │  User Pain     │   │  Trend Scout   │   │   Competitive      │
 │  Researcher    │   │                │   │   Intelligence     │
 └───────┬────────┘   └───────┬────────┘   └─────────┬──────────┘
         └────────────────────┼──────────────────────┘
                              ▼
                  ┌────────────────────────┐
                  │  Research Synthesizer   │  Cross-references findings,
                  │                        │  surfaces contradictions
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │        Critic          │◄─── Can send agents back
                  │                        │     with specific feedback
                  └───────────┬────────────┘
                              ▼
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
 ┌────────────────────┐             ┌────────────────────┐
 │ Strategy Architect  │            │  GTM Strategist     │
 └─────────┬──────────┘             └─────────┬──────────┘
           └──────────────┬───────────────────┘
                          ▼
              ┌────────────────────────┐
              │   Blueprint Compiler   │  Assembles the final
              │                        │  strategy document
              └────────────────────────┘
```

### The Critique Loop

The Critic agent evaluates research quality and can send specific agents back for revisions. This is what makes the system more than a pipeline.

1. Research agents produce their findings
2. Synthesizer combines everything
3. Critic evaluates: Are there gaps? Missing segments? Weak claims?
4. If gaps exist, the Critic hands off back to the Discovery Lead with specific instructions like *"The Researcher needs to investigate enterprise buyers"*
5. Discovery Lead re-dispatches only the flagged agents with the critique feedback
6. The revised work goes back through the Critic
7. Once approved, the system moves to strategy

This back-and-forth produces stronger output than a single pass.

## The 9 Agents

| # | Agent | What It Does |
|---|-------|-------------|
| 1 | **Discovery Lead** | Orchestrator. Decides which agents to call, when to request critique, how to respond to feedback |
| 2 | User Pain Researcher | Identifies user segments, pain points, and jobs-to-be-done |
| 3 | Trend Scout | Analyzes industry trends, timing windows, and answers "why now?" |
| 4 | Competitive Intelligence | Maps competitors, assesses moats, identifies market gaps |
| 5 | Research Synthesizer | Cross-references all research, surfaces contradictions, ranks insights |
| 6 | **Critic** | Evaluates work quality. Approves or sends specific agents back with targeted feedback |
| 7 | Strategy Architect | Builds product vision, strategic bets, moat strategy, sequencing |
| 8 | GTM Strategist | Builds go-to-market: beachhead segment, positioning, channels, pricing, launch phases |
| 9 | Blueprint Compiler | Compiles all work into a polished Product Strategy Blueprint |

## SDK Patterns Used

| Pattern | Where |
|---------|-------|
| **Agent-as-Tool** | Discovery Lead calls 7 specialist agents as tools |
| **Bidirectional Handoff** | Discovery Lead and Critic transfer control back and forth |
| **Parallel Tool Calls** | Discovery Lead dispatches 3 research agents at once |

## Output

The final deliverable is a Product Strategy Blueprint with:
- Executive Summary
- Research Foundation (user segments, pain points, trends, competitive landscape)
- Synthesis and Key Insights
- Strategic Direction (vision, bets, moat, sequencing)
- Go-to-Market (beachhead, positioning, channels, pricing, launch phases)
- Risks and Open Questions
- Agent Deliberation Log (what the Critic pushed back on and what changed)

## Setup

```bash
git clone <repo-url>
cd Multi-agent-systems/product-strategy-forge

python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# Add your OpenAI API key to .env
```

## Run

Terminal mode (fully autonomous):
```bash
python forge.py "Your problem statement here"
```

Streamlit UI (with human-in-the-loop at each phase):
```bash
streamlit run app.py
```

## Project Structure

```
product-strategy-forge/
├── forge_agents/
│   ├── lead.py              # Discovery Lead (7 tools + Critic handoff)
│   ├── researcher.py        # User Pain Researcher
│   ├── trend_scout.py       # Trend Scout
│   ├── competitive.py       # Competitive Intelligence
│   ├── synthesizer.py       # Research Synthesizer
│   ├── critic.py            # Critic (bidirectional handoff with Discovery Lead)
│   ├── strategist.py        # Strategy Architect
│   ├── gtm.py               # GTM Strategist
│   └── compiler.py          # Blueprint Compiler
├── forge.py                 # Terminal runner
├── app.py                   # Streamlit UI
├── config.py                # Configuration
├── requirements.txt
└── .env.example
```

## Tech Stack

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) for agent framework
- GPT-4o powering all 9 agents
- Streamlit for the human-in-the-loop UI
- Python 3.11+
