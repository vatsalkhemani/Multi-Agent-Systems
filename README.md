# Multi-Agent Systems

A collection of multi-agent AI systems exploring different orchestration patterns — collaborative, adversarial, and critique-driven. Each project is a standalone system with its own agents, UI, and architecture.

## Projects

| Project | Agents | Pattern | Tech |
|---------|--------|---------|------|
| [Product Strategy Forge](product-strategy-forge/) | 9 | Collaborative + cross-provider critique | GPT-4o + Gemini Critic, OpenAI Agents SDK, Streamlit |
| [Product Strategy Solo](product-strategy-solo/) | 8 | Collaborative, single-pass | GPT-4o, OpenAI Agents SDK, Streamlit |
| [Debate Arena](debate-arena/) | 6 | Adversarial, multi-round debate | GPT-4o, OpenAI Agents SDK, Streamlit |

### Product Strategy Forge

9 agents collaborate to turn a problem statement into a Product Strategy Blueprint. Three researchers work in parallel, a synthesizer cross-references their findings, and a Gemini-powered Critic challenges GPT-4o's work — sending agents back to redo weak sections. Human approval gates between phases.

**Key patterns:** Agent-as-tool, bidirectional handoffs, parallel execution, critique loops, cross-provider challenge (GPT-4o + Gemini)

### Product Strategy Solo

Same pipeline as the Forge, minus the Critic. Single-pass baseline — no redo loops, no cross-provider challenge, no approval gates. Exists for direct comparison against the Forge to see what critique catches.

### Debate Arena

6 agents engage in structured adversarial debate across 3 rounds. A Moderator frames two opposing positions, Advocate Alpha and Beta argue their sides, and a Devil's Advocate attacks both. Agents cross-examine each other's specific claims, then defend under fire. A Judge scores all arguments, and a Synthesizer compiles a Decision Brief.

**Key patterns:** Adversarial agents, multi-round protocol, cross-examination, scored evaluation, emergent quality through conflict

## Quick Start

Each project is independent. Pick one and run:

```bash
cd <project-name>
pip install -r requirements.txt
streamlit run app.py          # Interactive UI
```

Or run in terminal mode:

```bash
python forge.py "your prompt"    # Product Strategy Forge
python solo.py "your prompt"     # Product Strategy Solo
python arena.py "your prompt"    # Debate Arena
```

## Setup

All projects use Azure OpenAI. Create a `.env` in the repo root:

```env
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
GEMINI_API_KEY=your-gemini-key  # Only needed for Product Strategy Forge
```

## Stack

- **Orchestration:** OpenAI Agents SDK
- **LLMs:** Azure OpenAI (GPT-4o), Google Gemini (Critic in Forge)
- **UI:** Streamlit with real-time agent activity streaming
- **Concurrency:** Thread-safe shared state with daemon threads
