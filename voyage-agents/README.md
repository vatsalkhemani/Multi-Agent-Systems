# Voyage Agents

**7 AI agents that research, plan, review, and build an interactive travel guide website — from a single trip idea.**

> Project 1 (Forge): Agents that think together. Project 2 (Arena): Agents that argue. **Project 3 (Voyage): Agents that BUILD.**

## What It Does

Give Voyage Agents a destination, group size, budget, and vibe. It deploys a research team, planners, a quality reviewer, and a web developer — then hands you a complete interactive HTML travel guide you can open in your browser and share with friends.

**Input:** "Bali, 5 days, 4 friends, $600/person, chill beach vibes with great food"

**Output:** A beautiful, mobile-first HTML website with:
- Interactive day-by-day itinerary (expandable cards)
- Curated venue cards with ratings, costs, tags, and Google Maps links
- Leaflet.js interactive map with color-coded markers
- Budget breakdown dashboard
- Logistics cheat sheet

## Architecture

```
User Input (destination, dates, group, budget, vibe)
                        │
┌───────────── PHASE 1: RESEARCH (parallel) ──────────────┐
│                                                          │
│  🌍 Destination      ⭐ Experience     🚗 Logistics     │
│     Researcher          Curator           Planner        │
│                                                          │
│  Culture, weather,   Restaurants,      Flights,          │
│  visa, safety,       cafes, bars,      transport,        │
│  neighborhoods       activities,       accommodation,    │
│                      beaches           money tips        │
│                      (with coords!)                      │
│                                                          │
│               ↓ Trip Reviewer (Gemini) ↓                 │
│          Quality check — approve or send back            │
└────────────────────────┬─────────────────────────────────┘
                         │
┌───────────── PHASE 2: PLANNING (sequential) ────────────┐
│                                                          │
│  📅 Itinerary Architect                                 │
│  Day-by-day, time-slotted plan with real venues          │
│                         ↓                                │
│  💰 Budget Analyst                                      │
│  Per-person breakdown, splurge vs save, money tips       │
└────────────────────────┬─────────────────────────────────┘
                         │
┌───────────── PHASE 3: BUILD ────────────────────────────┐
│                                                          │
│  🌐 Website Builder                                     │
│  Assembles everything into a stunning single-file HTML   │
│  with Leaflet maps, venue cards, budget dashboard        │
└────────────────────────┬─────────────────────────────────┘
                         │
                    📄 Complete HTML file
                    Open in browser. Share with friends.
```

## The 7 Agents

| Agent | Role | Model |
|-------|------|-------|
| **Trip Director** | Orchestrator — manages workflow, dispatches agents | GPT-4o |
| **Destination Researcher** | Deep research — culture, weather, visa, neighborhoods | GPT-4o |
| **Experience Curator** | Finds restaurants, bars, activities, beaches with coordinates & costs | GPT-4o |
| **Logistics Planner** | Flights, transport, accommodation, money tips | GPT-4o |
| **Itinerary Architect** | Builds realistic day-by-day, time-slotted plan | GPT-4o |
| **Budget Analyst** | Per-person breakdown, splurge vs save, hidden costs | GPT-4o |
| **Trip Reviewer** | Quality check — catches unrealistic timing, gaps, budget misalignment | Gemini |
| **Website Builder** | Assembles all data into interactive HTML travel guide | GPT-4o |

## What Makes It Genuinely Agentic

- **Adaptive research** — Bali gets different coverage than rural Bhutan
- **Interest-based curation** — "chill beach vibes" produces different venues than "adventure and adrenaline"
- **Constraint satisfaction** — the Itinerary Architect solves geographic clustering, energy management, and meal timing
- **Budget trade-offs** — the analyst suggests where to splurge vs save, not just sums
- **Cross-model review** — Gemini evaluates GPT-4o's work, catches different blind spots
- **Tangible output** — agents don't just deliberate, they BUILD a complete interactive website

## Quick Start

### Prerequisites

- Python 3.11+
- Azure OpenAI API access (GPT-4o)
- Google Gemini API key

### Setup

```bash
cd voyage-agents
pip install -r requirements.txt
```

Create a `.env` file in the project root (or use the shared one):

```env
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
GEMINI_API_KEY=your-gemini-key
```

### Run (Terminal — autonomous)

```bash
python voyage.py "Bali, 5 days, 4 friends, $600/person, chill beach vibes"
```

Output saved to `output_travel_guide.html` — open in your browser.

### Run (Streamlit — interactive with human-in-the-loop)

```bash
streamlit run app.py
```

Fill in your trip details, describe your vibe, and watch 7 agents collaborate in real time. Approve between phases. Download your travel guide.

## Key Architectural Patterns

| Pattern | How It's Used |
|---------|---------------|
| **Agent-as-Tool** | Director calls specialists as tools for structured dispatch |
| **Parallel Execution** | 3 research agents run simultaneously in Phase 1 |
| **Bidirectional Handoff** | Director ↔ Reviewer for quality gate with redo loop |
| **Cross-Model Critique** | Gemini reviews GPT-4o's work for genuine second opinion |
| **Artifact Generation** | Agents produce a tangible, shareable HTML website |
| **Human-in-the-Loop** | Approval gates between phases with optional guidance |

## Project Structure

```
voyage-agents/
├── app.py                    # Streamlit UI (interactive mode)
├── voyage.py                 # Terminal runner (autonomous mode)
├── config.py                 # Azure OpenAI + Gemini client setup
├── requirements.txt
├── README.md
└── voyage_agents/
    ├── __init__.py
    ├── director.py           # Trip Director (orchestrator)
    ├── researcher.py         # Destination Researcher
    ├── curator.py            # Experience Curator
    ├── logistics.py          # Logistics Planner
    ├── itinerary.py          # Itinerary Architect
    ├── budget.py             # Budget Analyst
    ├── reviewer.py           # Trip Reviewer (Gemini)
    └── builder.py            # Website Builder
```

## Tech Stack

- **Orchestration**: OpenAI Agents SDK
- **Primary LLM**: Azure OpenAI GPT-4o
- **Cross-Model Review**: Google Gemini
- **UI**: Streamlit with real-time activity streaming
- **Output**: Self-contained HTML with Leaflet.js maps

---

*Part of the [Multi-Agent Systems](../) portfolio — showcasing collaborative, adversarial, and constructive multi-agent patterns.*
