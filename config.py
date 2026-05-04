import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"   # or "mixtral-8x7b-32768"

# ── Domain configs ─────────────────────────────────────────────────────────────
DOMAINS = {
    "System Design": {
        "icon": "🏗️",
        "description": "Distributed systems, scalability, architecture trade-offs",
        "topics": ["load balancing", "caching", "databases", "microservices",
                   "message queues", "CDN", "rate limiting", "CAP theorem"],
        "time_per_question": 10,   # minutes
    },
    "Machine Learning": {
        "icon": "🤖",
        "description": "ML concepts, model evaluation, practical ML pipelines",
        "topics": ["overfitting", "gradient descent", "transformers", "RAG",
                   "feature engineering", "bias-variance", "evaluation metrics"],
        "time_per_question": 8,
    },
    "Python / DSA": {
        "icon": "🐍",
        "description": "Data structures, algorithms, Python internals",
        "topics": ["arrays", "trees", "graphs", "dynamic programming",
                   "sorting", "Python GIL", "async/await", "generators"],
        "time_per_question": 12,
    },
    "Frontend (React)": {
        "icon": "⚛️",
        "description": "React, state management, performance, browser internals",
        "topics": ["virtual DOM", "hooks", "reconciliation", "useEffect",
                   "code splitting", "SSR vs CSR", "accessibility"],
        "time_per_question": 8,
    },
    "Behavioral (STAR)": {
        "icon": "💬",
        "description": "Situational questions using the STAR framework",
        "topics": ["conflict resolution", "leadership", "failure stories",
                   "ownership", "collaboration", "ambiguity", "impact"],
        "time_per_question": 6,
    },
}

DIFFICULTIES = {
    "Junior (0–2 yrs)": {
        "label": "junior",
        "description": "Fundamental concepts, clear explanations expected",
        "num_questions": 4,
    },
    "Mid-level (2–5 yrs)": {
        "label": "mid",
        "description": "Depth expected, trade-offs and real scenarios",
        "num_questions": 5,
    },
    "Senior (5+ yrs)": {
        "label": "senior",
        "description": "Leadership, design decisions, vague problems",
        "num_questions": 6,
    },
}

# ── Scoring rubric dimensions ──────────────────────────────────────────────────
RUBRIC = {
    "Technical Accuracy": "Is the answer factually correct and precise?",
    "Depth & Completeness": "Does it cover edge cases, trade-offs, and nuance?",
    "Communication Clarity": "Is it well-structured and easy to understand?",
    "Practical Awareness": "Does the candidate show real-world experience?",
}
