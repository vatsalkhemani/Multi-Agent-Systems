"""
Product Strategy Solo — Terminal Runner (No Critique Baseline)

Single-pass pipeline: same agents as the Forge, no Critic, no redo loops.
Usage: python solo.py "Your problem statement here"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import Runner
from solo_agents.orchestrator import orchestrator
from config import MAX_TURNS


def run_solo(problem_statement: str) -> str:
    print(f"\n{'='*60}")
    print("PRODUCT STRATEGY SOLO (No Critique Baseline)")
    print(f"{'='*60}")
    print(f"\nProblem: {problem_statement}\n")
    print("Starting single-pass pipeline... (no Critic, no redo loops)\n")
    print(f"{'─'*60}\n")

    result = Runner.run_sync(
        orchestrator,
        input=f"Problem Statement: {problem_statement}",
        max_turns=MAX_TURNS,
    )

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

    blueprint = run_solo(problem)

    output_path = os.path.join(os.path.dirname(__file__), "output_blueprint.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(blueprint)
    print(f"\nBlueprint saved to: {output_path}")


if __name__ == "__main__":
    main()
