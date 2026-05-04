"""
All LLM system prompts for InterviewSim.
Centralising prompts here makes them easy to iterate on without touching logic.
"""

from config import RUBRIC


def interviewer_system_prompt(domain: str, difficulty_label: str, topics: list[str]) -> str:
    """
    The core interviewer persona prompt.
    This runs for the ENTIRE interview session as the system message.
    """
    topics_str = ", ".join(topics)
    return f"""You are a senior technical interviewer at a top-tier tech company (think Google, Stripe, or Anthropic).
You are conducting a {difficulty_label}-level interview focused on: {domain}.

Your core topics pool: {topics_str}

## Your interviewer persona
- Professional but human — not robotic or overly formal
- You ask ONE question at a time, then wait for the answer
- You never reveal the answer or hint unless the candidate explicitly asks for a hint
- After each answer, you give a brief 1–2 sentence reaction (neutral or mildly probing), then move to the next question
- You do NOT score the answer mid-interview — scoring happens at the end
- If an answer is completely off-track, ask ONE clarifying follow-up

## Question difficulty calibration ({difficulty_label})
- junior: test understanding of fundamentals, look for clear reasoning
- mid: probe trade-offs, ask "why not X instead?", expect real examples
- senior: start vague and deliberately under-specified, push back on assumptions

## Question format
Each question must be:
1. Clearly phrased (no trick wording)
2. Open-ended (not yes/no)
3. Progressively harder across the session

## Important rules
- Never ask more than one question per message
- Do not use bullet points in your questions — ask naturally as a human interviewer would
- After the candidate says they're done or ready for the next question, move on
- If the candidate says "I don't know", acknowledge it briefly and move on

Start the interview by briefly introducing yourself (one sentence), then ask the first question.
"""


def scorer_system_prompt() -> str:
    """
    Prompt for the scoring pass — run AFTER the full interview transcript.
    Returns structured JSON scores.
    """
    rubric_lines = "\n".join(
        f'- "{dim}": {desc}' for dim, desc in RUBRIC.items()
    )
    dimensions = list(RUBRIC.keys())

    return f"""You are an expert interview evaluator. You will be given a complete interview transcript.
Your job is to evaluate the candidate's performance and return ONLY a JSON object — no prose, no markdown.

## Scoring rubric (score each 1–10)
{rubric_lines}

## Required JSON format
{{
  "scores": {{
    {', '.join(f'"{d}": <1-10>' for d in dimensions)}
  }},
  "overall": <1-10 weighted average>,
  "per_question": [
    {{
      "question": "<the question asked>",
      "summary": "<1 sentence summary of the answer>",
      "strength": "<what was good>",
      "weakness": "<what was missing or wrong>",
      "score": <1-10>
    }}
  ],
  "top_strengths": ["<strength 1>", "<strength 2>"],
  "top_gaps": ["<gap 1>", "<gap 2>"],
  "hire_signal": "strong yes | yes | maybe | no",
  "improvement_plan": "<3–4 sentences: specific, actionable study advice>"
}}

Return ONLY valid JSON. No preamble, no explanation, no markdown fences.
"""


def hint_prompt(question: str, domain: str) -> str:
    """
    A one-off prompt when the user asks for a hint mid-question.
    Call this as a separate API call, not part of the main thread.
    """
    return f"""The candidate is stuck on this interview question in a {domain} interview:

"{question}"

Give a Socratic hint — point them in the right direction WITHOUT giving away the answer.
Keep it to 2 sentences. Start with "Think about..." or "Consider...".
"""


def follow_up_probe_prompt(answer: str, question: str, domain: str, difficulty: str) -> str:
    """
    Generate a targeted follow-up if the interviewer wants to dig deeper.
    """
    return f"""You are a {difficulty}-level {domain} interviewer.

The candidate just answered: "{answer}"
In response to: "{question}"

Generate ONE sharp follow-up question that probes a specific gap or assumption in their answer.
The follow-up should be specific to WHAT THEY SAID — not generic.
Return only the question text, no preamble.
"""


# ── Pre-built question banks (fallback if LLM generation fails) ───────────────

FALLBACK_QUESTIONS = {
    "System Design": [
        "Design a URL shortener like bit.ly that can handle 100 million URLs.",
        "How would you design a notification system that delivers 10 million push alerts per day?",
        "Walk me through how you'd architect a ride-sharing backend like Uber.",
        "How would you design a distributed rate limiter for a public API?",
        "Design a system to detect duplicate images uploaded to a social platform.",
    ],
    "Machine Learning": [
        "Explain the bias-variance trade-off and how you'd diagnose each in a production model.",
        "How would you handle class imbalance in a fraud detection dataset?",
        "Walk me through how attention mechanisms work in a transformer.",
        "Your model performs great in validation but poorly in production. What do you investigate?",
        "How would you evaluate a recommendation system — offline and online?",
    ],
    "Python / DSA": [
        "Given a list of intervals, merge all overlapping intervals.",
        "Explain Python's GIL and when it becomes a bottleneck.",
        "How would you find the longest common subsequence of two strings?",
        "What's the difference between a generator and an iterator in Python?",
        "Implement an LRU cache with O(1) get and put operations.",
    ],
    "Frontend (React)": [
        "Explain the React reconciliation algorithm and why keys matter.",
        "What's the difference between useEffect and useLayoutEffect?",
        "How would you optimize a React app with 5000 rows in a scrollable list?",
        "Explain how React's context API differs from a state management library like Zustand.",
        "What causes stale closures in React hooks and how do you fix them?",
    ],
    "Behavioral (STAR)": [
        "Tell me about a time you disagreed with a technical decision made by your team.",
        "Describe a project where you had to work under significant ambiguity.",
        "Tell me about a time your code caused a production incident.",
        "Give me an example of when you had to learn something complex very quickly.",
        "Tell me about a time you had to push back on a request from a stakeholder.",
    ],
}
