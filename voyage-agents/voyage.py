"""
Voyage Agents - Terminal Runner

Run this to test the full agentic flow end-to-end.
Usage: python voyage.py "Bali, 5 days, 4 friends, $600/person, chill beach vibes with great food"
"""

import sys
import os
import re
import json
import concurrent.futures

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import Agent, Runner
from config import MODEL, GEMINI_MODEL, MAX_TURNS


def _run_agent_sync(agent, input_text):
    """Run a single agent synchronously (for use in thread pool)."""
    result = Runner.run_sync(agent, input=input_text, max_turns=10)
    return result.final_output


def run_voyage(trip_request: str) -> str:
    """Run the full Voyage Agents pipeline."""
    from voyage_agents.researcher import destination_researcher
    from voyage_agents.curator import experience_curator
    from voyage_agents.logistics import logistics_planner
    from voyage_agents.itinerary import itinerary_architect
    from voyage_agents.budget import budget_analyst
    from voyage_agents.reviewer import trip_reviewer
    from voyage_agents.builder import website_builder

    print(f"\n{'='*60}", flush=True)
    print("VOYAGE AGENTS", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"\nTrip Request:\n{trip_request}\n", flush=True)

    trip_input = "Trip Request:\n" + trip_request

    # -- Phase 1: Research (3 agents in parallel) --
    print(f"{'-'*60}", flush=True)
    print("PHASE 1: Research (3 agents in parallel)", flush=True)
    print(f"{'-'*60}\n", flush=True)

    # Run 3 research agents in parallel using threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        f_research = executor.submit(_run_agent_sync, destination_researcher, trip_input)
        f_curator = executor.submit(_run_agent_sync, experience_curator, trip_input)
        f_logistics = executor.submit(_run_agent_sync, logistics_planner, trip_input)

    research_out = f_research.result()
    curator_out = f_curator.result()
    logistics_out = f_logistics.result()
    print(f"  Destination Researcher: {len(research_out)} chars", flush=True)
    print(f"  Experience Curator:     {len(curator_out)} chars", flush=True)
    print(f"  Logistics Planner:      {len(logistics_out)} chars", flush=True)

    full_research = (
        "=== DESTINATION RESEARCH ===\n" + research_out
        + "\n\n=== CURATED EXPERIENCES ===\n" + curator_out
        + "\n\n=== LOGISTICS PLAN ===\n" + logistics_out
    )

    # -- Phase 1b: Review (Gemini) --
    print(f"\n{'-'*60}", flush=True)
    print("PHASE 1b: Trip Review (Gemini)", flush=True)
    print(f"{'-'*60}\n", flush=True)

    simple_reviewer = Agent(
        name="Trip Reviewer",
        model=GEMINI_MODEL,
        instructions="""You are a meticulous trip quality reviewer. Review the research below.
Evaluate: realism, completeness, budget alignment, vibe match, group suitability, geographic sense.
If issues exist, note what the specific agent should fix.
Give a Trip Quality Score: X/10. Be specific, reference agents by name.""",
    )

    try:
        review_result = Runner.run_sync(simple_reviewer, input=trip_input + "\n\n" + full_research, max_turns=5)
        review_out = review_result.final_output
        print(f"  Trip Reviewer: {len(review_out)} chars", flush=True)
    except Exception as e:
        print(f"  Trip Reviewer skipped (Gemini error: {str(e)[:80]})", flush=True)
        review_out = "Review skipped due to API limits. Proceeding with research as-is."

    # -- Phase 2: Itinerary --
    print(f"\n{'-'*60}", flush=True)
    print("PHASE 2: Itinerary", flush=True)
    print(f"{'-'*60}\n", flush=True)

    itinerary_input = trip_input + "\n\nAPPROVED RESEARCH:\n" + full_research + "\n\nREVIEWER NOTES:\n" + review_out
    itinerary_result = Runner.run_sync(itinerary_architect, input=itinerary_input, max_turns=10)
    itinerary_out = itinerary_result.final_output
    print(f"  Itinerary Architect: {len(itinerary_out)} chars", flush=True)

    # -- Phase 2b: Budget --
    print(f"\n{'-'*60}", flush=True)
    print("PHASE 2b: Budget", flush=True)
    print(f"{'-'*60}\n", flush=True)

    budget_input = trip_input + "\n\nAPPROVED RESEARCH:\n" + full_research + "\n\nITINERARY:\n" + itinerary_out
    budget_result = Runner.run_sync(budget_analyst, input=budget_input, max_turns=10)
    budget_out = budget_result.final_output
    print(f"  Budget Analyst: {len(budget_out)} chars", flush=True)

    # -- Phase 3: Build Website --
    print(f"\n{'-'*60}", flush=True)
    print("PHASE 3: Build Website", flush=True)
    print(f"{'-'*60}\n", flush=True)

    build_input = (
        trip_input
        + "\n\n" + full_research
        + "\n\n=== ITINERARY ===\n" + itinerary_out
        + "\n\n=== BUDGET ===\n" + budget_out
        + "\n\n=== REVIEWER NOTES ===\n" + review_out
    )

    build_result = Runner.run_sync(website_builder, input=build_input, max_turns=10)
    html_out = build_result.final_output
    print(f"  Website Builder: {len(html_out)} chars", flush=True)

    return html_out


def build_html(json_str: str) -> str:
    """Inject the builder's JSON output into the HTML template."""
    from voyage_agents.template import HTML_TEMPLATE

    # Clean markdown fences if present
    json_str = re.sub(r'^```\w*\n', '', json_str.strip())
    json_str = re.sub(r'\n```\s*$', '', json_str.strip())

    # Extract JSON object
    match = re.search(r'(\{.*\})', json_str, re.DOTALL)
    if match:
        json_str = match.group(1)

    # Parse to validate, then re-serialize for clean injection
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse error: {e}", flush=True)
        print(f"  Attempting to use raw JSON string...", flush=True)
        data = None

    if data:
        clean_json = json.dumps(data, ensure_ascii=False)
        title = data.get("destination", "Trip") + " Travel Guide"
        primary = data.get("primary_color", "#7DB8D4")
        primary_light = data.get("primary_light", "#A8D8EA")
    else:
        clean_json = json_str
        title = "Travel Guide"
        primary = "#7DB8D4"
        primary_light = "#A8D8EA"

    html = HTML_TEMPLATE
    html = html.replace("{{TRIP_DATA}}", clean_json)
    html = html.replace("{{TITLE}}", title)
    html = html.replace("{{PRIMARY_COLOR}}", primary)
    html = html.replace("{{PRIMARY_LIGHT}}", primary_light)

    return html


def main():
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        print("Enter your trip details below.")
        print("Include: destination, duration, group size, budget, and vibe.\n")
        request = input("Trip request: ").strip()
        if not request:
            request = (
                "Destination: Sri Lanka\n"
                "Duration: 5 days\n"
                "Group: 6 friends\n"
                "Budget: $800 per person\n"
                "Interests: surfing, food, nightlife\n"
                "Vibe: Chill beach mornings with surfing, great cafes for long lunches, "
                "sunset cocktails at beach clubs, and a couple of wild nights out. "
                "Mix of Weligama and Mirissa. We want hidden gems, not tourist traps."
            )
            print(f"\nUsing default request.\n")

    json_output = run_voyage(request)
    html = build_html(json_output)

    # Save output
    output_path = os.path.join(os.path.dirname(__file__), "output_travel_guide.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nTravel guide saved to: {output_path}")
    print("Open it in your browser to view the interactive guide!")


if __name__ == "__main__":
    main()
