import streamlit as st
from groq import Groq

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="SmartBot",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# STYLES
# -----------------------------
st.markdown("""
<style>
.chat-container {
    max-width: 900px;
    margin: auto;
}
.user-msg {
    background: #1e293b;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
}
.bot-msg {
    background: #020617;
    padding: 12px;
    border-radius: 12px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------
st.title("🤖 SmartBot")
st.caption("Independent AI Assistant")

# -----------------------------
# CLIENT
# -----------------------------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are SmartBot, an independent AI assistant. Never mention APIs, models, or providers."
        }
    ]

# -----------------------------
# RENDER CHAT
# -----------------------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-msg'>🧑 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>🤖 {msg['content']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# INPUT
# -----------------------------
user_input = st.chat_input("Ask SmartBot...")

# -----------------------------
# RESPONSE HANDLER
# -----------------------------
def get_smartbot_reply(messages):
    try:
        response = client.responses.create(
            model="llama-4-scout",
            input=[{"role": m["role"], "content": m["content"]} for m in messages],
            max_output_tokens=800
        )
        return response.output_text
    except Exception:
        return "SmartBot is temporarily unavailable. Please try again."

# -----------------------------
# CHAT LOGIC
# -----------------------------
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    reply = get_smartbot_reply(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
