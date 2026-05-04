# 🎯 InterviewSim

AI-powered mock technical interviews with real-time scoring and improvement plans.

## Features
- 5 domains: System Design, ML, Python/DSA, Frontend, Behavioral
- 3 difficulty levels: Junior, Mid, Senior
- Streaming interviewer responses (feels live)
- Hint system (Socratic — doesn't give away answers)
- Post-interview rubric scoring across 4 dimensions
- Per-question breakdown with strengths/weaknesses
- Personalized study plan

## Quick start

```bash
# 1. Clone and enter the project
cd interviewsim

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 4. Run
streamlit run app.py
```

## Architecture

```
User picks domain + difficulty
        ↓
Streamlit session state owns message history
        ↓
Each answer → Anthropic API (full history sent each turn)
        ↓
Interview ends → separate scoring API call (different system prompt)
        ↓
JSON scores → rendered in Results page
```

## Stack
- `anthropic` — Claude claude-sonnet-4-20250514 for interviewer + scorer
- `streamlit` — UI and session state
- `python-dotenv` — env config
- `fpdf2` — PDF report (Day 5)
