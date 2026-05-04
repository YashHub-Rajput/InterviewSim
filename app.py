"""
app.py — InterviewSim entry point.
This IS the Day 1 working product:
  - Domain + difficulty picker
  - Starts the interview session
  - Full streaming chat interface
  - "End interview" → triggers scoring
  - Score displayed inline
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import DOMAINS, DIFFICULTIES, RUBRIC
from interviewsim.interviewer import chat_turn, score_interview, get_hint, build_transcript

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InterviewSim",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session state defaults ─────────────────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "setup",        # setup | interview | results
        "domain": None,
        "difficulty": None,
        "messages": [],          # Anthropic-format message history
        "question_count": 0,
        "max_questions": 5,
        "scores": None,
        "current_question": "",  # tracks last interviewer question for hint
        "hint_shown": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — SETUP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "setup":
    st.title("🎯 InterviewSim")
    st.caption("AI-powered mock interviews with real-time scoring")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Domain")
        domain_choice = st.radio(
            "Pick a domain",
            options=list(DOMAINS.keys()),
            format_func=lambda d: f"{DOMAINS[d]['icon']} {d}",
            label_visibility="collapsed",
        )
        st.caption(DOMAINS[domain_choice]["description"])

    with col2:
        st.subheader("Difficulty")
        difficulty_choice = st.radio(
            "Pick difficulty",
            options=list(DIFFICULTIES.keys()),
            label_visibility="collapsed",
        )
        diff = DIFFICULTIES[difficulty_choice]
        st.caption(diff["description"])
        st.caption(f"**{diff['num_questions']} questions**")

    st.divider()

    # Preview topics
    with st.expander("📋 Topics that may be covered"):
        topics = DOMAINS[domain_choice]["topics"]
        cols = st.columns(3)
        for i, t in enumerate(topics):
            cols[i % 3].markdown(f"- {t}")

    st.write("")
    if st.button("Start Interview →", type="primary", use_container_width=True):
        st.session_state.domain = domain_choice
        st.session_state.difficulty = difficulty_choice
        st.session_state.max_questions = diff["num_questions"]
        st.session_state.phase = "interview"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "interview":
    domain = st.session_state.domain
    difficulty_key = st.session_state.difficulty
    diff_label = DIFFICULTIES[difficulty_key]["label"]
    topics = DOMAINS[domain]["topics"]
    max_q = st.session_state.max_questions

    # Header
    col_a, col_b, col_c = st.columns([3, 1, 1])
    with col_a:
        st.markdown(f"### {DOMAINS[domain]['icon']} {domain} Interview")
        st.caption(f"{difficulty_key}")
    with col_b:
        q_count = st.session_state.question_count
        st.metric("Questions", f"{q_count} / {max_q}")
    with col_c:
        if st.button("End Interview", type="secondary"):
            st.session_state.phase = "results"
            st.rerun()

    st.divider()

    # ── Render existing chat history ──
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(msg["content"])

    # ── Auto-start: if no messages yet, trigger the opening ──
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            # Send an empty "begin" user message to get the interviewer to open
            bootstrap_messages = [{"role": "user", "content": "Let's begin the interview."}]
            for chunk in chat_turn(bootstrap_messages, domain, diff_label, topics, stream=True):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        # Store the opening (skip the bootstrap user message — not part of real history)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.current_question = full_response
        st.session_state.question_count = 1
        st.rerun()

    # ── Hint button ──
    if st.session_state.current_question and not st.session_state.hint_shown:
        if st.button("💡 Get a hint for this question"):
            hint = get_hint(st.session_state.current_question, domain)
            st.info(f"**Hint:** {hint}")
            st.session_state.hint_shown = True

    # ── User answer input ──
    answer = st.chat_input("Type your answer here…")
    if answer:
        # Display user message
        with st.chat_message("user"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "user", "content": answer})
        st.session_state.hint_shown = False

        # Check if we've hit max questions
        if st.session_state.question_count >= max_q:
            wrap_up = "Thank you — that was the final question. You've completed the interview. Type 'done' when you're ready to see your results."
            with st.chat_message("assistant"):
                st.markdown(wrap_up)
            st.session_state.messages.append({"role": "assistant", "content": wrap_up})
            st.session_state.phase = "results"
            st.rerun()

        # Get next interviewer message
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in chat_turn(
                st.session_state.messages, domain, diff_label, topics, stream=True
            ):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.current_question = full_response
        st.session_state.question_count += 1
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "results":
    st.title("📊 Interview Results")

    domain = st.session_state.domain
    difficulty_key = st.session_state.difficulty

    # Run scoring if not done yet
    if st.session_state.scores is None:
        with st.spinner("Analysing your interview… this takes ~10 seconds"):
            transcript = build_transcript(
                st.session_state.messages,
                domain,
                difficulty_key,
            )
            st.session_state.scores = score_interview(transcript)

    scores = st.session_state.scores

    if "error" in scores:
        st.error(f"Scoring error: {scores.get('raw', 'Unknown error')}")
    else:
        # ── Overall verdict ──
        hire = scores.get("hire_signal", "unknown")
        hire_colors = {
            "strong yes": "🟢",
            "yes": "🟡",
            "maybe": "🟠",
            "no": "🔴",
            "unknown": "⚪",
        }
        st.markdown(f"## {hire_colors.get(hire, '⚪')} Hire signal: **{hire.upper()}**")
        st.metric("Overall Score", f"{scores.get('overall', 0)} / 10")
        st.divider()

        # ── Rubric dimension scores ──
        st.subheader("Rubric breakdown")
        dim_scores = scores.get("scores", {})
        if dim_scores:
            cols = st.columns(len(dim_scores))
            for i, (dim, score) in enumerate(dim_scores.items()):
                with cols[i]:
                    st.metric(dim, f"{score}/10")
                    st.progress(score / 10)

        st.divider()

        # ── Per-question breakdown ──
        st.subheader("Question-by-question")
        for i, q in enumerate(scores.get("per_question", []), 1):
            with st.expander(f"Q{i}: {q.get('question', '')[:80]}… — {q.get('score', '?')}/10"):
                st.markdown(f"**Your answer (summary):** {q.get('summary', '')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"✅ {q.get('strength', '')}")
                with col2:
                    st.warning(f"⚠️ {q.get('weakness', '')}")

        st.divider()

        # ── Strengths and gaps ──
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top strengths")
            for s in scores.get("top_strengths", []):
                st.success(f"✅ {s}")
        with col2:
            st.subheader("Gaps to fix")
            for g in scores.get("top_gaps", []):
                st.warning(f"⚠️ {g}")

        st.divider()

        # ── Improvement plan ──
        st.subheader("Study plan")
        st.info(scores.get("improvement_plan", ""))

    # ── Restart button ──
    st.divider()
    if st.button("🔄 Start a new interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
