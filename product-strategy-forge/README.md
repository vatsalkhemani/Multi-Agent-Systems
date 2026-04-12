# Product Strategy Forge

A multi-agent system where 9 specialized AI agents collaborate to turn a problem statement into a comprehensive Product Strategy Blueprint  - with human-in-the-loop approval at every phase.

## What This Is

Imagine giving a problem statement like "SMBs can't manage social media" and getting back a full strategy document  - user segments with pain severity scores, competitive landscape with moat assessments, strategic bets with risk analysis, a go-to-market plan with channel economics, and an executive summary a VP could act on. All stress-tested by a Critic running on a completely different LLM.

Nine agents with distinct roles research, debate, critique, and refine. Three researchers run in parallel, a Synthesizer cross-references their findings, and a Gemini-powered Critic challenges GPT-4o's work  - sending specific agents back to redo weak sections. You approve between phases and can steer with guidance. The output is a polished, presentation-ready Product Strategy Blueprint.

### Screenshots

![Product Strategy Blueprint output](screenshots/image.png)

![Agents working in real-time](screenshots/run3.png)

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
                  │       (Gemini)         │     with specific feedback
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

This is what makes the system more than a pipeline. The Critic runs on Gemini  - a different LLM  - so it doesn't share GPT-4o's blind spots.

1. Research agents produce their findings
2. Synthesizer combines everything
3. Critic evaluates: Are there gaps? Missing segments? Weak claims?
4. If gaps exist, the Critic hands off back to the Discovery Lead with specific instructions like *"The Researcher needs to investigate enterprise buyers"*
5. Discovery Lead re-dispatches only the flagged agents with the critique feedback
6. Once approved, the system moves to strategy

### The 3 Phases (with Human Approval)

| Phase | What Happens | You Decide |
|-------|-------------|------------|
| **1. Research & Critique** | 3 researchers run in parallel, synthesizer cross-references, critic evaluates (up to 2 redo rounds) | Review research, add guidance for strategy |
| **2. Strategy & Critique** | Strategy Architect builds vision + bets, GTM Strategist plans go-to-market, critic evaluates (up to 1 redo round) | Review strategy, add guidance for blueprint |
| **3. Blueprint** | Blueprint Compiler assembles everything into a polished strategy document | Download the final `.md` file |

## The 9 Agents

| # | Agent | What It Does | Model |
|---|-------|-------------|-------|
| 1 | **Discovery Lead** | Orchestrator  - decides which agents to call, when to request critique, how to respond to feedback | GPT-4o |
| 2 | User Pain Researcher | Identifies user segments, pain points, and jobs-to-be-done | GPT-4o |
| 3 | Trend Scout | Analyzes industry trends, timing windows, and answers "why now?" | GPT-4o |
| 4 | Competitive Intelligence | Maps competitors, assesses moats, identifies market gaps | GPT-4o |
| 5 | Research Synthesizer | Cross-references all research, surfaces contradictions, ranks insights | GPT-4o |
| 6 | **Critic** | Evaluates work quality using a different LLM. Approves or sends specific agents back | Gemini |
| 7 | Strategy Architect | Builds product vision, strategic bets, moat strategy, sequencing | GPT-4o |
| 8 | GTM Strategist | Go-to-market: beachhead, positioning, channels, pricing, launch phases | GPT-4o |
| 9 | Blueprint Compiler | Compiles all work into a polished Product Strategy Blueprint | GPT-4o |

## The Output

A professional Product Strategy Blueprint with:
- Executive Summary
- Research Foundation (user segments, pain points, trends, competitive landscape)
- Synthesis and Key Insights
- Strategic Direction (vision, bets, moat, sequencing)
- Go-to-Market (beachhead, positioning, channels, pricing, launch phases)
- Risks and Open Questions
- Agent Deliberation Log (what the Critic pushed back on and what changed)

## Setup

```bash
cd product-strategy-forge
pip install -r requirements.txt
```

Create a `.env` file:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (default: `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2024-12-01-preview`) |
| `GEMINI_API_KEY` | Google Gemini API key (powers the Critic agent) |

## Run

```bash
streamlit run app.py                        # Interactive UI with approval gates
python forge.py "your problem statement"    # Autonomous terminal mode
```

### Sample Prompts

> Mid-market e-commerce brands (50-500 employees) struggle to unify their product catalog, inventory, and pricing across 5+ sales channels. They waste 20+ hours/week on manual data sync and still ship wrong prices or oversell inventory.

> Engineering teams at Series B-D startups spend 30% of their sprint capacity on incident response, yet still have 4+ hour MTTR. Existing observability tools generate alert fatigue without actionable root-cause analysis.

> Remote teams of 10-50 people have no good way to run async standups and stay aligned on weekly goals without drowning in Slack messages and status meetings.

## Project Structure

```
product-strategy-forge/
├── forge_agents/
│   ├── lead.py              # Discovery Lead (7 tools + Critic handoff)
│   ├── researcher.py        # User Pain Researcher
│   ├── trend_scout.py       # Trend Scout
│   ├── competitive.py       # Competitive Intelligence
│   ├── synthesizer.py       # Research Synthesizer
│   ├── critic.py            # Critic (Gemini, bidirectional handoff)
│   ├── strategist.py        # Strategy Architect
│   ├── gtm.py               # GTM Strategist
│   └── compiler.py          # Blueprint Compiler
├── app.py                   # Streamlit UI
├── forge.py                 # Terminal runner
├── config.py                # Azure OpenAI + Gemini config
└── requirements.txt
```

## SDK Patterns Used

| Pattern | Where |
|---------|-------|
| **Agent-as-Tool** | Discovery Lead calls 7 specialist agents as tools |
| **Cross-Model Critique** | Critic runs on Gemini  - different LLM, different blind spots |
| **Bidirectional Handoff** | Discovery Lead ↔ Critic transfer control back and forth |
| **Parallel Tool Calls** | 3 research agents dispatched simultaneously |
| **RunHooks** | Streamlit UI streams agent activity in real-time |

## Tech Stack

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) for orchestration
- Azure OpenAI (GPT-4o) + Google Gemini for cross-model critique
- Streamlit for the human-in-the-loop UI
- Python 3.11+
