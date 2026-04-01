# Debate Arena

A multi-agent adversarial debate system that produces better decisions through structured argumentation. 6 AI agents with distinct roles engage in a 3-round debate protocol — arguing, attacking, defending, and judging — to transform any decision prompt into a comprehensive Decision Brief.

## Why Multi-Agent Debate?

A single LLM asked "should we build or buy?" produces a balanced but shallow analysis. It can't genuinely argue both sides because it collapses to the middle.

Debate Arena solves this by assigning **adversarial objectives** to separate agents:
- **Advocate Alpha** must WIN for Position A — no hedging allowed
- **Advocate Beta** must WIN for Position B — equally aggressive
- **Devil's Advocate** must DESTROY both — allergic to consensus
- The **Judge** scores argument quality impartially
- The **Synthesizer** distills the strongest insights from all sides

The result? **Round 3 arguments are qualitatively better than Round 1** because they've been stress-tested through cross-examination and forced rebuttals. This emergent quality improvement is impossible with single-pass analysis.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        DEBATE ARENA                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: OPENING ARGUMENTS                                     │
│  ┌─────────────┐                                                │
│  │  Moderator   │ ── Frames 2 opposing positions                │
│  └──────┬──────┘                                                │
│     ┌───┼────────────┐                                          │
│     ▼   ▼            ▼                                          │
│  ┌─────┐ ┌─────┐ ┌────────────┐                                │
│  │Alpha│ │Beta │ │Devil's Adv.│  (All three argue)              │
│  └─────┘ └─────┘ └────────────┘                                │
│         │                                                        │
│         ▼ HUMAN APPROVAL GATE                                    │
│                                                                  │
│  PHASE 2: CROSS-EXAMINATION & REBUTTALS                         │
│  ┌─────────────┐                                                │
│  │  Moderator   │                                               │
│  └──────┬──────┘                                                │
│         │  Round 2: Each agent attacks the others' arguments     │
│     ┌───┼────────────┐                                          │
│     ▼   ▼            ▼                                          │
│  ┌─────┐ ┌─────┐ ┌────────────┐                                │
│  │Alpha│ │Beta │ │Devil's Adv.│  (Cross-examine)                │
│  └─────┘ └─────┘ └────────────┘                                │
│         │                                                        │
│         │  Round 3: Each agent defends against attacks           │
│     ┌───┼────────────┐                                          │
│     ▼   ▼            ▼                                          │
│  ┌─────┐ ┌─────┐ ┌────────────┐                                │
│  │Alpha│ │Beta │ │Devil's Adv.│  (Rebut & defend)               │
│  └─────┘ └─────┘ └────────────┘                                │
│         │                                                        │
│         ▼ HUMAN APPROVAL GATE                                    │
│                                                                  │
│  PHASE 3: VERDICT & DECISION BRIEF                              │
│  ┌─────────────┐                                                │
│  │  Moderator   │                                               │
│  └──────┬──────┘                                                │
│     ┌───┴────┐                                                  │
│     ▼        ▼                                                  │
│  ┌──────┐ ┌────────────┐                                        │
│  │Judge │ │Synthesizer │  Judge scores → Synthesizer compiles   │
│  └──────┘ └────────────┘                                        │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │  DECISION BRIEF      │  Professional markdown document       │
│  └──────────────────────┘                                       │
└──────────────────────────────────────────────────────────────────┘
```

## The 6 Agents

| Agent | Role | Objective |
|-------|------|-----------|
| **Moderator** | Orchestrator | Frames positions, enforces debate protocol, passes context between agents |
| **Advocate Alpha** | Position A debater | WIN for Position A. Preempt objections, attack opponents, defend under fire |
| **Advocate Beta** | Position B debater | WIN for Position B. Same adversarial drive as Alpha, opposite conclusion |
| **Devil's Advocate** | Contrarian | DESTROY both positions. Find fatal flaws, hidden assumptions, Option C |
| **Judge** | Impartial scorer | Score all arguments on 5 criteria (Evidence, Logic, Feasibility, Risk, Persuasion) |
| **Synthesizer** | Brief compiler | Compile everything into a professional Decision Brief with recommendation |

## What's New vs. Product Strategy Forge

| Pattern | Product Strategy Forge | Debate Arena |
|---------|----------------------|--------------|
| Agent relationship | Collaborative | **Adversarial** |
| Quality mechanism | Critic sends back | **Cross-examination + rebuttals** |
| Interaction | Hub-and-spoke (Lead → agents) | **Agent vs. agent** (Alpha attacks Beta's arguments) |
| Rounds | Single pass + redo | **Multi-round with escalation** |
| Evaluation | Pass/fail critique | **Scored scorecard with 5 criteria** |
| Output improvement | Better after critique | **Provably better each round** |

## Setup

### Prerequisites
- Python 3.11+
- Azure OpenAI resource with GPT-4o deployment

### Installation

```bash
cd debate-arena
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root (or parent directory):

```env
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
MAX_TURNS=50
```

## Usage

### Streamlit UI (Interactive, Human-in-the-Loop)

```bash
streamlit run app.py
```

Features:
- Enter any decision prompt
- Watch agents debate in real-time via activity log
- Approve between phases with optional guidance
- Download the final Decision Brief as markdown

### Terminal (Autonomous)

```bash
python arena.py "Should we build or buy our ML platform?"
```

Or run interactively:
```bash
python arena.py
```

## Example Decision Prompts

- "Should we build our own ML infrastructure in-house or buy an existing platform? We're a 200-person B2B SaaS company with 5 ML engineers."
- "Should we expand internationally to Europe first or go deeper in the US market? We have $10M ARR and 500 customers."
- "Should we open-source our core SDK or keep it proprietary? We're a developer tools company with 2,000 paying users."
- "Should we hire a VP of Sales or promote our top AE? We're at $5M ARR and need to scale the sales org."

## Output: Decision Brief

The final output is a professional markdown document containing:

1. **Executive Summary** — VP-level decision recommendation
2. **Positions Debated** — Both sides with scores
3. **Debate Dynamics** — How arguments evolved through cross-examination
4. **Recommendation** — Evidence-based path forward with conditions
5. **Risk Register** — All risks from all debaters, ranked
6. **Open Questions** — What still needs validation
7. **Scorecard** — Full argument quality scores
8. **Deliberation Log** — How the adversarial process improved the output

## Tech Stack

- **Orchestration**: OpenAI Agents SDK (agent-as-tool pattern)
- **LLM**: Azure OpenAI GPT-4o
- **UI**: Streamlit with real-time activity streaming
- **Concurrency**: Thread-safe shared state with daemon threads
