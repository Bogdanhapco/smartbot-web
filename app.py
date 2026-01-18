import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="SmartBot",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
.chat-box {
    background: #0f1117;
    padding: 20px;
    border-radius: 15px;
}
.user {
    color: #00ffcc;
}
.bot {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 SmartBot")
st.caption("Independent AI System")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are SmartBot. Never mention any external AI provider."}
    ]

for msg in st.session_state.messages[1:]:
    role_class = "user" if msg["role"] == "user" else "bot"
    st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)

user_input = st.chat_input("Ask SmartBot...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=st.session_state.messages,
        temperature=0.7
    )

    bot_reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    st.rerun()
