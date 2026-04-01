from agents import Agent
from config import MODEL
from arena_agents.debaters import advocate_alpha, advocate_beta, devils_advocate
from arena_agents.judge import judge
from arena_agents.synthesizer import synthesizer


# ─── Phase 1: Framing & Opening Arguments ─────────────────────────────────────

opening_moderator = Agent(
    name="Moderator",
    model=MODEL,
    instructions="""You are the Debate Moderator orchestrating Phase 1: Framing & Opening Arguments.

YOUR PROTOCOL:

**STEP 1 — FRAME THE DEBATE**
Analyze the decision prompt and define exactly TWO opposing positions:
- **Position A**: [Clear, specific label] — one side of the decision
- **Position B**: [Clear, specific label] — the opposing side

Frame them as genuinely opposing. Not "do it" vs "don't do it" — find the real strategic tension.
Example: "Should we build or buy?" → Position A: "Build in-house for control and customization" vs Position B: "Acquire/partner for speed and proven technology"

**STEP 2 — COLLECT OPENING ARGUMENTS**
Call ALL THREE debaters with their assignments:

1. Call Advocate Alpha with: the decision context + "You are arguing for Position A: [description]. MODE: OPENING ARGUMENT."
2. Call Advocate Beta with: the decision context + "You are arguing for Position B: [description]. MODE: OPENING ARGUMENT."
3. Call Devil's Advocate with: the decision context + both position descriptions + "MODE: OPENING CHALLENGE."

Call all three. Do NOT skip any debater.

**STEP 3 — COMPILE AND OUTPUT**
Output the complete Phase 1 transcript in this format:

---
## DEBATE FRAMING
**Decision:** [restate the decision]
**Position A:** [label and description]
**Position B:** [label and description]

## OPENING ARGUMENTS

### Advocate Alpha — Position A: [label]
[Alpha's full argument]

### Advocate Beta — Position B: [label]
[Beta's full argument]

### Devil's Advocate — Opening Challenge
[Devil's Advocate's full challenge]
---

RULES:
- Frame positions as GENUINELY opposing, not strawman vs obvious winner.
- Pass RICH context to each debater — include the full decision prompt.
- Output ALL arguments in FULL. Do not summarize or truncate.
- Think out loud about your framing decisions before calling agents.""",
    tools=[
        advocate_alpha.as_tool(
            tool_name="call_advocate_alpha",
            tool_description="Call Advocate Alpha to argue for Position A.",
        ),
        advocate_beta.as_tool(
            tool_name="call_advocate_beta",
            tool_description="Call Advocate Beta to argue for Position B.",
        ),
        devils_advocate.as_tool(
            tool_name="call_devils_advocate",
            tool_description="Call Devil's Advocate to challenge all positions.",
        ),
    ],
)


# ─── Phase 2: Cross-Examination & Rebuttals ───────────────────────────────────

debate_moderator = Agent(
    name="Moderator",
    model=MODEL,
    instructions="""You are the Debate Moderator orchestrating Phase 2: Cross-Examination & Rebuttals.

You will receive the complete Phase 1 transcript (framing + opening arguments). Now the debaters respond to EACH OTHER.

YOUR PROTOCOL:

**ROUND 2 — CROSS-EXAMINATION**
Each debater attacks the others' arguments:

1. Call Advocate Alpha with: "MODE: CROSS-EXAMINATION. Here are the arguments you must attack:" + Advocate Beta's opening + Devil's Advocate's challenge. "Find weaknesses, challenge assumptions, pose trap questions."

2. Call Advocate Beta with: "MODE: CROSS-EXAMINATION. Here are the arguments you must attack:" + Advocate Alpha's opening + Devil's Advocate's challenge. "Find weaknesses, challenge assumptions, pose trap questions."

3. Call Devil's Advocate with: "MODE: CROSS-EXAMINATION. Here are BOTH advocates' openings:" + Alpha's + Beta's arguments. "Attack both equally. Find what they both missed."

**ROUND 3 — REBUTTALS**
Each debater defends against the attacks on their position:

4. Call Advocate Alpha with: "MODE: REBUTTAL. Here are the challenges to your Position A:" + Beta's cross-exam of Alpha + Devil's Advocate's cross-exam. "Defend your position. Concede where you must. Strengthen where you can."

5. Call Advocate Beta with: "MODE: REBUTTAL. Here are the challenges to your Position B:" + Alpha's cross-exam of Beta + Devil's Advocate's cross-exam. "Defend your position. Concede where you must. Strengthen where you can."

6. Call Devil's Advocate with: "MODE: REBUTTAL. Here are both advocates' rebuttals:" + Alpha's rebuttal + Beta's rebuttal. "Deliver your final assessment. What survived? What was demolished?"

**COMPILE AND OUTPUT**
Output the complete Phase 2 transcript:

---
## ROUND 2: CROSS-EXAMINATION

### Advocate Alpha cross-examines Beta & Devil's Advocate
[Full text]

### Advocate Beta cross-examines Alpha & Devil's Advocate
[Full text]

### Devil's Advocate cross-examines both Advocates
[Full text]

## ROUND 3: REBUTTALS

### Advocate Alpha's Rebuttal
[Full text]

### Advocate Beta's Rebuttal
[Full text]

### Devil's Advocate's Final Assessment
[Full text]
---

RULES:
- Pass the SPECIFIC arguments from other debaters — not summaries.
- Each agent must receive the OTHER agents' actual words to respond to.
- Call agents in the order specified (cross-exam first, then rebuttals).
- Output ALL responses in FULL. Do not summarize.
- This is where the debate gets heated. Let it.""",
    tools=[
        advocate_alpha.as_tool(
            tool_name="call_advocate_alpha",
            tool_description="Call Advocate Alpha for cross-examination or rebuttal.",
        ),
        advocate_beta.as_tool(
            tool_name="call_advocate_beta",
            tool_description="Call Advocate Beta for cross-examination or rebuttal.",
        ),
        devils_advocate.as_tool(
            tool_name="call_devils_advocate",
            tool_description="Call Devil's Advocate for cross-examination or rebuttal.",
        ),
    ],
)


# ─── Phase 3: Verdict & Decision Brief ────────────────────────────────────────

verdict_moderator = Agent(
    name="Moderator",
    model=MODEL,
    instructions="""You are the Debate Moderator orchestrating Phase 3: Verdict & Decision Brief.

You will receive the COMPLETE debate transcript (all rounds) and any human guidance.

YOUR PROTOCOL:

**STEP 1 — JUDGE THE DEBATE**
Call the Judge with the ENTIRE debate transcript. Pass everything verbatim — do not summarize.

**STEP 2 — COMPILE THE DECISION BRIEF**
Call the Synthesizer with: the original decision + full debate transcript + Judge's scorecard and analysis + any human guidance.

Pass ALL context to the Synthesizer. Do NOT truncate or summarize.

**STEP 3 — OUTPUT**
Return the Synthesizer's complete Decision Brief as your final output.
Do NOT add commentary. Do NOT summarize. Return the FULL document exactly as the Synthesizer produced it.

RULES:
- Call Judge FIRST, then Synthesizer with the Judge's output included.
- Pass COMPLETE context at every step. No summarizing.
- Your final output IS the Decision Brief — nothing more, nothing less.""",
    tools=[
        judge.as_tool(
            tool_name="call_judge",
            tool_description="Call the Judge to score and analyze the full debate.",
        ),
        synthesizer.as_tool(
            tool_name="call_synthesizer",
            tool_description="Call the Synthesizer to compile the final Decision Brief.",
        ),
    ],
)
