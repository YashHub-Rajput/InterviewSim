"""
app.py — InterviewSim entry point.
This IS the Day 1 working product:
  - Domain + difficulty picker
  - Starts the interview session
  - Full streaming chat interface
  - "End interview" → triggers scoring
  - Score displayed inline
"""
from interviewsim.report import generate_pdf
import streamlit as st
import time
import streamlit.components.v1 as components
import sys, os
# sys.path.insert(0, os.path.dirname(__file__))

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
        "question_start_time": None,
        "last_audio_bytes": None,
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

    # ── Timer ──────────────────────────────────────────────────────────────────
    time_per_q = DOMAINS[domain]["time_per_question"] * 60  # convert to seconds
    start = st.session_state.question_start_time or time.time()
    elapsed = int(time.time() - start)
    remaining = max(0, time_per_q - elapsed)

    components.html(f"""
    <div style="font-family: sans-serif; padding: 8px 4px">
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px">
        <span id="timer-label" style="font-size:13px; color:#888888">⏱ Time remaining</span>
        <span id="timer-text" style="font-size:24px; font-weight:700; font-variant-numeric:tabular-nums; color:#1D9E75">--:--</span>
    </div>
    <div style="background:#dddddd; border-radius:6px; height:8px; width:100%; overflow:hidden">
        <div id="timer-bar" style="height:100%; border-radius:6px; width:100%; background:#1D9E75; transition: width 1s linear, background 1s linear"></div>
    </div>
    </div>

    <script>
    var remaining = {remaining};
    var total = {time_per_q};

    function formatTime(s) {{
        var m = Math.floor(s / 60);
        var sec = s % 60;
        return m + ":" + (sec < 10 ? "0" : "") + sec;
    }}

    function getColor(s) {{
        var pct = s / total;
        if (pct > 0.5) return "#1D9E75";
        if (pct > 0.25) return "#EF9F27";
        return "#D85A30";
    }}

    function render() {{
        var color = getColor(remaining);
        var pct = Math.round((remaining / total) * 100);
        document.getElementById("timer-text").innerText = formatTime(remaining);
        document.getElementById("timer-text").style.color = color;
        document.getElementById("timer-bar").style.width = pct + "%";
        document.getElementById("timer-bar").style.background = color;
        if (remaining <= 0) {{
        document.getElementById("timer-label").innerText = "⏰ Time's up — wrap up!";
        document.getElementById("timer-label").style.color = "#D85A30";
        }}
    }}

    render();

    if (remaining > 0) {{
        var interval = setInterval(function() {{
        remaining--;
        render();
        if (remaining <= 0) clearInterval(interval);
        }}, 1000);
    }}
    </script>
    """, height=90, scrolling=False)
    

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
        st.session_state.question_start_time = time.time() 
        st.rerun()

    # ── Hint button ──
    if st.session_state.current_question and not st.session_state.hint_shown:
        if st.button("💡 Get a hint for this question"):
            hint = get_hint(st.session_state.current_question, domain)
            st.info(f"**Hint:** {hint}")
            st.session_state.hint_shown = True

    # ── User answer input ──
    from interviewsim.voice import transcribe

    # ── Input: text or voice ──
    col_input, col_mic = st.columns([5, 1])

    with col_input:
        answer = st.chat_input("Type your answer here…")

    with col_mic:
        audio = st.audio_input("🎙️")
        submit_voice = st.button("Send 🎤")

    # 🎙️ Voice handling (FIXED)
    if audio and submit_voice:
        audio_bytes = audio.read()

        # Only process NEW audio
        if audio_bytes != st.session_state.last_audio_bytes:
            st.session_state.last_audio_bytes = audio_bytes

            with st.spinner("Transcribing…"):
                voice_text = transcribe(audio_bytes)

            if voice_text:
                st.info(f"🎙️ You said: *{voice_text}*")
                answer = voice_text

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
        st.session_state.question_start_time = time.time()
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
        import plotly.graph_objects as go

        st.subheader("Rubric breakdown")
        dim_scores = scores.get("scores", {})
        if dim_scores:
            dims = list(dim_scores.keys())
            vals = list(dim_scores.values())
            vals_closed = vals + [vals[0]]
            dims_closed = dims + [dims[0]]

            fig = go.Figure(go.Scatterpolar(
                r=vals_closed,
                theta=dims_closed,
                fill="toself",
                fillcolor="rgba(127, 119, 221, 0.2)",
                line=dict(color="rgba(127, 119, 221, 0.9)", width=2),
                marker=dict(size=6),
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=10)),
                    angularaxis=dict(tickfont=dict(size=12)),
                ),
                showlegend=False,
                margin=dict(t=20, b=20, l=40, r=40),
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            cols = st.columns(len(dim_scores))
            for i, (dim, score) in enumerate(dim_scores.items()):
                with cols[i]:
                    st.metric(dim.split()[0], f"{score}/10")

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

    pdf_bytes = generate_pdf(scores, domain, difficulty_key)
    st.download_button(
    label="📄 Download PDF Report",
    data=pdf_bytes,
    file_name=f"interviewsim_{domain.replace(' ','_').lower()}_report.pdf",
    mime="application/pdf",
    use_container_width=True,
)
