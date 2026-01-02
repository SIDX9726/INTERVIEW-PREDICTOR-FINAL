import streamlit as st
import time
from rag import ask_pdf
import asyncio

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Interview Outcome Assistant",
    page_icon="📄",
    layout="centered"
)

# ---------------- EVENT LOOP FIX ----------------
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ---------------- SESSION STATE ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_value" not in st.session_state:
    st.session_state.input_value = ""

if "mode" not in st.session_state:
    st.session_state.mode = "Failure Insights ❌"

if "stage" not in st.session_state:
    st.session_state.stage = "All Stages"

# ---------------- CALLBACK ----------------
def select_query(text):
    st.session_state.input_value = text

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📄 Interview RAG")
    st.caption("Evidence-based interview insights")
    st.markdown("---")

    # Mode
    st.session_state.mode = st.radio(
        "Insight Mode",
        ["Failure Insights ❌", "Success Insights ✅"]
    )

    # 🔥 Feature 2: Interview Stage Filter
    st.session_state.stage = st.selectbox(
        "Interview Stage",
        [
            "All Stages",
            "Online Assessment (OA)",
            "Technical Interview",
            "HR / Managerial",
            "Post-Interview (Ghosting / Offers)"
        ]
    )

    st.markdown("---")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.input_value = ""
        st.rerun()

# ---------------- HEADER ----------------
st.markdown("## 🎯 Interview Outcome Assistant")
st.caption(
    "Answers strictly from real interview failures and success stories."
)

# ---------------- SUGGESTED QUESTIONS ----------------
st.markdown("### 🔍 Suggested Questions")

examples = [
    "Why do candidates get rejected after clearing OA?",
    "Why do companies ghost after interviews?",
    "Skills actually required to get selected",
    "Common mistakes freshers make in interviews",
    "Patterns seen in successful candidates",
]

cols = st.columns(2)
for i, q in enumerate(examples):
    cols[i % 2].button(
        q,
        use_container_width=True,
        on_click=select_query,
        args=(q,)
    )

st.markdown("---")

# ---------------- INPUT ----------------
question = st.text_area(
    "Ask your question",
    value=st.session_state.input_value,
    placeholder="e.g. Why do candidates fail after technical rounds?",
    height=90
)

ask = st.button("🚀 Ask Assistant", use_container_width=True, type="primary")

# ---------------- CONFIDENCE BREAKDOWN (Feature 4) ----------------
def confidence_breakdown(answer: str):
    words = len(answer.split())

    evidence = "High" if words > 150 else "Medium" if words > 70 else "Low"
    coverage = "Medium"  # based on retriever k
    specificity = "High" if ":" in answer or "-" in answer else "Medium"

    return {
        "Evidence Strength": evidence,
        "Coverage Across Cases": coverage,
        "Specificity": specificity
    }

# ---------------- FOLLOW-UP CONTEXT ----------------
def contextualize(new_q: str):
    if not st.session_state.chat_history:
        return new_q

    last_q = st.session_state.chat_history[-1]["question"]
    if new_q.lower().startswith(("why", "how", "explain", "what about")):
        return f"Previous question: {last_q}\nFollow-up: {new_q}"

    return new_q

# ---------------- ASK LOGIC ----------------
if ask:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("🔍 Analyzing interview cases..."):
            start = time.time()

            q = contextualize(question)

            # Mode + Stage injection
            prefix = ""
            if st.session_state.mode.startswith("Failure"):
                prefix += "Based on failure cases only. "
            else:
                prefix += "Based on success stories only. "

            if st.session_state.stage != "All Stages":
                prefix += f"Focus on {st.session_state.stage}. "

            final_query = prefix + q

            answer = ask_pdf(final_query)
            elapsed = time.time() - start
            confidence = confidence_breakdown(answer)

        st.session_state.chat_history.append({
            "question": question,
            "answer": answer,
            "time": elapsed,
            "confidence": confidence,
            "mode": st.session_state.mode,
            "stage": st.session_state.stage
        })

        st.session_state.input_value = ""
        st.rerun()

# ---------------- CHAT ----------------
if st.session_state.chat_history:
    st.markdown("## 💬 Conversation")

    for chat in reversed(st.session_state.chat_history):

        st.markdown(
            f"""
            <div style="
                background-color: var(--secondary-background-color);
                padding: 12px;
                border-radius: 10px;">
                <strong>🧑 You</strong><br>{chat['question']}
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("🤖 Assistant", expanded=True):
            st.write(chat["answer"])

            st.markdown("**📊 Confidence Breakdown**")
            for k, v in chat["confidence"].items():
                st.write(f"- {k}: {v}")

            st.caption(
                f"Mode: {chat['mode']} | Stage: {chat['stage']} | "
                f"⏱️ {chat['time']:.2f}s"
            )

            # 🔥 Feature 1: Actionable Improvement Plan
            if st.button("🔧 What should I improve?", key=chat["question"]):
                improvement_q = (
                    "Based on the above insights, suggest 3–5 actionable "
                    "improvement steps for a student."
                )
                st.write(ask_pdf(improvement_q))

            # 🔥 Feature 5: Follow-up Suggestions
            st.markdown("**👉 You may also ask:**")
            followups = [
                "How can freshers avoid this?",
                "What skills should I focus on next?",
                "Which interview stage is most critical here?"
            ]

            for f in followups:
                if st.button(f, key=f + chat["question"]):
                    st.session_state.input_value = f
                    st.rerun()

        st.markdown("---")

# ---------------- FOOTER ----------------
st.caption(
    "⚠️ Answers are strictly derived from real interview data. "
    "If information is missing, the system does not guess."
)
