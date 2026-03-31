"""
Product Strategy Forge — Terminal Runner

Run this to test the full agentic flow end-to-end.
Usage: python forge.py "Your problem statement here"
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import Runner
from forge_agents.lead import discovery_lead
from config import MAX_TURNS


def run_forge(problem_statement: str) -> str:
    """Run the full Product Strategy Forge autonomously."""
    print(f"\n{'='*60}")
    print("PRODUCT STRATEGY FORGE")
    print(f"{'='*60}")
    print(f"\nProblem: {problem_statement}\n")
    print("Starting Discovery Lead... (agents will orchestrate autonomously)\n")
    print(f"{'─'*60}\n")

    result = Runner.run_sync(
        discovery_lead,
        input=f"Problem Statement: {problem_statement}",
        max_turns=MAX_TURNS,
    )

    print(f"\n{'─'*60}")
    print(f"Forge complete. Final output:\n")

    final_output = result.final_output
    print(final_output)

    return final_output


def main():
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        problem = input("Enter your problem statement: ").strip()
        if not problem:
            problem = "Small and medium businesses struggle to manage their social media presence effectively. They lack the time, expertise, and budget for dedicated social media managers, resulting in inconsistent posting, poor engagement, and missed growth opportunities."
            print(f"\nUsing default problem: {problem}\n")

    blueprint = run_forge(problem)

    # Save output
    output_path = os.path.join(os.path.dirname(__file__), "output_blueprint.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(blueprint)
    print(f"\nBlueprint saved to: {output_path}")


if __name__ == "__main__":
    main()
