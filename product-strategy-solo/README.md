# Product Strategy Solo (No Critique Baseline)

Single-pass product strategy pipeline. Same agents as the [Product Strategy Forge](../product-strategy-forge/), minus the Critic. No redo loops, no cross-provider challenge, no human approval gates. One model, one pass, one shot.

**Purpose:** This exists as a baseline to demonstrate the value of multi-model critique. Run the same problem statement through both Solo and Forge, compare the outputs, and see what the Critic catches that the single-pass misses.

## Architecture

```
Problem Statement
       │
┌──────▼──────┐
│ Orchestrator │
└──────┬──────┘
   ┌───┼───────────┐
   ▼   ▼           ▼
┌─────┐ ┌───────┐ ┌──────────────┐
│User │ │Trend  │ │Competitive   │  (Research — parallel)
│Pain │ │Scout  │ │Intelligence  │
└──┬──┘ └──┬────┘ └──────┬───────┘
   └────────┼─────────────┘
            ▼
    ┌───────────────┐
    │  Synthesizer  │
    └───────┬───────┘
            ▼
    ┌───────────────┐
    │  Strategy     │
    │  Architect    │
    └───────┬───────┘
            ▼
    ┌───────────────┐
    │ GTM Strategist│
    └───────┬───────┘
            ▼
    ┌───────────────┐
    │  Blueprint    │
    │  Compiler     │
    └───────────────┘
            │
            ▼
    Product Strategy Blueprint
```

## What's Different from the Forge

| | Solo (this) | Forge |
|---|---|---|
| Agents | 8 (GPT-4o only) | 9 (GPT-4o + Gemini Critic) |
| Critique | None | Gemini challenges GPT-4o's work |
| Redo loops | None | Up to 2 research redos, 1 strategy redo |
| Human gates | None | Approval between phases |
| Model diversity | Single model | Cross-provider (different biases) |

## Setup

Same `.env` as the Forge — only needs Azure OpenAI keys (no Gemini).

```bash
cd product-strategy-solo
pip install -r requirements.txt
streamlit run app.py          # Interactive UI
python solo.py                # Terminal mode
```

## Usage

Run the same problem statement in both:

```bash
# Baseline (no critique)
cd product-strategy-solo
python solo.py "SMBs struggle to manage social media effectively"

# With critique
cd ../product-strategy-forge
python forge.py "SMBs struggle to manage social media effectively"
```

Compare the outputs side by side.
