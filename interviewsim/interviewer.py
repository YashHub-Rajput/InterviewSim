import json
from groq import Groq
from config import GROQ_API_KEY, MODEL
from interviewsim.prompts import (
    interviewer_system_prompt, scorer_system_prompt,
    hint_prompt, follow_up_probe_prompt,
)

client = Groq(api_key=GROQ_API_KEY)


def chat_turn(messages, domain, difficulty_label, topics, stream=True):
    system = interviewer_system_prompt(domain, difficulty_label, topics)
    all_messages = [{"role": "system", "content": system}] + messages
    if stream:
        return _stream_response(all_messages)
    else:
        response = client.chat.completions.create(
            model=MODEL, max_tokens=1000, messages=all_messages
        )
        return response.choices[0].message.content


def _stream_response(messages):
    stream = client.chat.completions.create(
        model=MODEL, max_tokens=1000, messages=messages, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def score_interview(transcript):
    messages = [
        {"role": "system", "content": scorer_system_prompt()},
        {"role": "user", "content": f"Here is the complete interview transcript:\n\n{transcript}"}
    ]
    response = client.chat.completions.create(
        model=MODEL, max_tokens=2000, messages=messages
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "error": "parse failed", "raw": raw, "overall": 0,
            "scores": {}, "per_question": [], "top_strengths": [],
            "top_gaps": [], "hire_signal": "unknown",
            "improvement_plan": "Scoring failed. Please retry."
        }


def get_hint(question, domain):
    r = client.chat.completions.create(
        model=MODEL, max_tokens=200,
        messages=[{"role": "user", "content": hint_prompt(question, domain)}]
    )
    return r.choices[0].message.content


def get_follow_up(answer, question, domain, difficulty):
    r = client.chat.completions.create(
        model=MODEL, max_tokens=200,
        messages=[{"role": "user", "content": follow_up_probe_prompt(answer, question, domain, difficulty)}]
    )
    return r.choices[0].message.content


def build_transcript(messages, domain, difficulty):
    lines = ["INTERVIEW TRANSCRIPT", f"Domain: {domain} | Difficulty: {difficulty}", "="*50, ""]
    for msg in messages:
        role = "INTERVIEWER" if msg["role"] == "assistant" else "CANDIDATE"
        lines.append(f"[{role}]\n{msg['content']}\n")
    return "\n".join(lines)