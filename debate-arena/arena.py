"""
Debate Arena — Terminal Runner

Run this to test the full adversarial debate end-to-end.
Usage: python arena.py "Your decision prompt here"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import Runner
from arena_agents.moderator import opening_moderator, debate_moderator, verdict_moderator
from config import MAX_TURNS


def run_arena(decision_prompt: str) -> str:
    print(f"\n{'='*60}")
    print("DEBATE ARENA")
    print(f"{'='*60}")
    print(f"\nDecision: {decision_prompt}\n")

    # Phase 1: Opening Arguments
    print(f"{'─'*60}")
    print("PHASE 1: Framing & Opening Arguments")
    print(f"{'─'*60}\n")

    result1 = Runner.run_sync(
        opening_moderator,
        input=f"DECISION TO DEBATE: {decision_prompt}",
        max_turns=MAX_TURNS,
    )
    opening_output = result1.final_output
    print(opening_output)
    print(f"\n{'─'*60}")
    print("Phase 1 complete. Starting cross-examination...")
    print(f"{'─'*60}\n")

    # Phase 2: Cross-Examination & Rebuttals
    print(f"{'─'*60}")
    print("PHASE 2: Cross-Examination & Rebuttals")
    print(f"{'─'*60}\n")

    context2 = (f"DECISION: {decision_prompt}\n\n"
                f"PHASE 1 TRANSCRIPT (Opening Arguments):\n{opening_output}\n\n")

    result2 = Runner.run_sync(
        debate_moderator,
        input=context2,
        max_turns=MAX_TURNS,
    )
    debate_output = result2.final_output
    print(debate_output)
    print(f"\n{'─'*60}")
    print("Phase 2 complete. Rendering verdict...")
    print(f"{'─'*60}\n")

    # Phase 3: Verdict & Decision Brief
    print(f"{'─'*60}")
    print("PHASE 3: Verdict & Decision Brief")
    print(f"{'─'*60}\n")

    context3 = (f"DECISION: {decision_prompt}\n\n"
                f"PHASE 1 — OPENING ARGUMENTS:\n{opening_output}\n\n"
                f"PHASE 2 — CROSS-EXAMINATION & REBUTTALS:\n{debate_output}\n\n")

    result3 = Runner.run_sync(
        verdict_moderator,
        input=context3,
        max_turns=MAX_TURNS,
    )
    brief = result3.final_output
    print(brief)

    return brief


def main():
    if len(sys.argv) > 1:
        decision = " ".join(sys.argv[1:])
    else:
        decision = input("Enter your decision prompt: ").strip()
        if not decision:
            decision = "Should we build our own ML infrastructure in-house or buy an existing platform like Databricks/SageMaker? We are a 200-person B2B SaaS company with 5 ML engineers, $2M annual cloud budget, and need to ship ML-powered features within 6 months."
            print(f"\nUsing default decision: {decision}\n")

    brief = run_arena(decision)

    output_path = os.path.join(os.path.dirname(__file__), "output_decision_brief.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(brief)
    print(f"\nDecision Brief saved to: {output_path}")


if __name__ == "__main__":
    main()
