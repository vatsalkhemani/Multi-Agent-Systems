# Debate Arena

A multi-agent adversarial debate system where 6 AI agents argue, attack, defend, and judge  - turning any decision into a comprehensive Decision Brief.

## What This Is

Ask a single LLM "should we build or buy?" and you get a balanced but shallow analysis. It hedges. It collapses to the middle. It can't genuinely argue both sides because it's one brain trying to hold two positions.

Debate Arena fixes this by giving separate agents adversarial objectives. Advocate Alpha must WIN for Position A  - no hedging. Advocate Beta must WIN for Position B  - equally aggressive. A Devil's Advocate tries to DESTROY both. They cross-examine each other's specific claims, then defend under fire. A Judge scores argument quality impartially, and a Synthesizer distills the strongest insights into a Decision Brief.

The result: Round 3 arguments are qualitatively better than Round 1 because they've been stress-tested through cross-examination and forced rebuttals. This emergent quality improvement is impossible with single-pass analysis.

## How It Works

```
  PHASE 1: OPENING ARGUMENTS
  ┌─────────────┐
  │  Moderator   │ ── Frames 2 opposing positions
  └──────┬──────┘
     ┌───┼────────────┐
     ▼   ▼            ▼
  ┌─────┐ ┌─────┐ ┌────────────┐
  │Alpha│ │Beta │ │Devil's Adv.│  (All three argue)
  └─────┘ └─────┘ └────────────┘
         │
         ▼ HUMAN APPROVAL GATE

  PHASE 2: CROSS-EXAMINATION & REBUTTALS
  ┌─────────────┐
  │  Moderator   │
  └──────┬──────┘
         │  Round 2: Each agent attacks the others
     ┌───┼────────────┐
     ▼   ▼            ▼
  ┌─────┐ ┌─────┐ ┌────────────┐
  │Alpha│ │Beta │ │Devil's Adv.│  (Cross-examine)
  └─────┘ └─────┘ └────────────┘
         │
         │  Round 3: Each agent defends against attacks
     ┌───┼────────────┐
     ▼   ▼            ▼
  ┌─────┐ ┌─────┐ ┌────────────┐
  │Alpha│ │Beta │ │Devil's Adv.│  (Rebut & defend)
  └─────┘ └─────┘ └────────────┘
         │
         ▼ HUMAN APPROVAL GATE

  PHASE 3: VERDICT
  ┌──────┐ ┌────────────┐
  │Judge │ │Synthesizer │  Judge scores → Synthesizer compiles
  └──────┘ └────────────┘
         │
         ▼
  ┌──────────────────────┐
  │   DECISION BRIEF     │
  └──────────────────────┘
```

### The 3 Phases (with Human Approval)

| Phase | What Happens | You Decide |
|-------|-------------|------------|
| **1. Opening Arguments** | Moderator frames 2 opposing positions, all 3 debaters argue | Review positions, add guidance |
| **2. Cross-Exam & Rebuttals** | Each agent attacks the others' arguments, then defends under fire | Review debate, steer direction |
| **3. Verdict** | Judge scores on 5 criteria, Synthesizer compiles Decision Brief | Download the final `.md` file |

## The 6 Agents

| # | Agent | Objective |
|---|-------|-----------|
| 1 | **Moderator** | Frames positions, enforces protocol, passes context between agents |
| 2 | **Advocate Alpha** | WIN for Position A. Preempt objections, attack opponents, defend under fire |
| 3 | **Advocate Beta** | WIN for Position B. Same adversarial drive, opposite conclusion |
| 4 | **Devil's Advocate** | DESTROY both positions. Find fatal flaws, hidden assumptions, Option C |
| 5 | **Judge** | Score all arguments on 5 criteria: Evidence, Logic, Feasibility, Risk, Persuasion |
| 6 | **Synthesizer** | Compile everything into a professional Decision Brief with recommendation |

## The Output

A professional Decision Brief with:
- Executive Summary  - VP-level decision recommendation
- Positions Debated  - both sides with scores
- Debate Dynamics  - how arguments evolved through cross-examination
- Recommendation  - evidence-based path forward with conditions
- Risk Register  - all risks from all debaters, ranked
- Scorecard  - full argument quality scores (5 criteria, 1-10 each)
- Deliberation Log  - how the adversarial process improved the output

## What's Different vs. Product Strategy Forge

| | Forge (collaborative) | Arena (adversarial) |
|---|---|---|
| Agent relationship | Agents help each other | **Agents attack each other** |
| Quality mechanism | Critic sends back for redo | **Cross-examination + rebuttals** |
| Interaction | Hub-and-spoke | **Agent vs. agent** |
| Evaluation | Pass/fail critique | **Scored scorecard (5 criteria)** |
| Output improvement | Better after critique | **Provably better each round** |

## Setup

```bash
cd debate-arena
pip install -r requirements.txt
```

Create a `.env` file:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (default: `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2024-12-01-preview`) |

## Run

```bash
streamlit run app.py                                          # Interactive UI
python arena.py "Should we build or buy our ML platform?"     # Terminal mode
```

### Sample Decision Prompts

> Should we build our own ML infrastructure in-house or buy an existing platform? We're a 200-person B2B SaaS company with 5 ML engineers.

> Should we expand internationally to Europe first or go deeper in the US market? We have $10M ARR and 500 customers.

> Should we open-source our core SDK or keep it proprietary? We're a developer tools company with 2,000 paying users.

## Project Structure

```
debate-arena/
├── arena_agents/
│   ├── moderator.py         # 3 phase-specific Moderators
│   ├── debaters.py          # Advocate Alpha, Beta, Devil's Advocate
│   ├── judge.py             # Judge (5-criteria scorecard)
│   └── synthesizer.py       # Synthesizer (Decision Brief compiler)
├── app.py                   # Streamlit UI
├── arena.py                 # Terminal runner
├── config.py                # Azure OpenAI config
└── requirements.txt
```

## Tech Stack

- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) for orchestration
- Azure OpenAI (GPT-4o)
- Streamlit for the human-in-the-loop UI
- Python 3.11+
