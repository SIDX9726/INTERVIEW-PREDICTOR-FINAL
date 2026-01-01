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

# ---------------- CALLBACK ----------------
def select_query(text):
    st.session_state.input_value = text

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📄 Interview RAG")
    st.caption("Answers from real interview cases")
    st.markdown("---")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.input_value = ""
        st.rerun()

# ---------------- HEADER ----------------
st.markdown("## 🎯 Interview Outcome Assistant")
st.caption("Understand interview outcomes using real-world cases.")

# ---------------- SUGGESTED QUESTIONS ----------------
st.markdown("### 🔍 Suggested Questions")

examples = [
    "Why do candidates get rejected after clearing OA?",
    "No response even after interview rounds",
    "Skills required to get selected",
    "Common interview mistakes",
]

cols = st.columns(2)
for i, q in enumerate(examples):
    cols[i % 2].button(q, use_container_width=True, on_click=select_query, args=(q,))

st.markdown("---")

# ---------------- INPUT ----------------
question = st.text_area(
    "Ask your question",
    value=st.session_state.input_value,
    placeholder="e.g. Why do candidates fail after technical rounds?",
    height=90
)

ask = st.button("🚀 Ask Assistant", use_container_width=True, type="primary")

# ---------------- ASK LOGIC ----------------
if ask:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("🔍 Searching interview cases..."):
            start = time.time()
            answer = ask_pdf(question)
            elapsed = time.time() - start

        st.session_state.chat_history.append({
            "question": question,
            "answer": answer,
            "time": elapsed,
        })
        st.session_state.input_value = ""
        st.rerun()

# ---------------- CHAT ----------------
if st.session_state.chat_history:
    st.markdown("## 💬 Conversation")

    for chat in reversed(st.session_state.chat_history):

        # Question bubble
        st.markdown(
            f"""
            <div style="
                background-color: var(--secondary-background-color);
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 6px;">
                <strong>🧑 You</strong><br>{chat['question']}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Answer with typewriter effect
        with st.expander("🤖 Assistant", expanded=True):
            placeholder = st.empty()
            text = chat["answer"]
            rendered = ""

            for ch in text:
                rendered += ch
                placeholder.markdown(rendered)
                time.sleep(0.003)

            st.caption(f"⏱️ Response time: {chat['time']:.2f}s")

        st.markdown("---")
