import os
import re
import urllib.request
import urllib.parse
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter
import streamlit as st
from gtts import gTTS
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="SmartBot AI Pro", layout="centered")

# Custom CSS for better UI
st.markdown("""
<style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; }
    .stButton>button { border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

class SmartEngine:
    def search_web(self, query):
        """Pro Model Search Engine"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, re.S)
                if snippets:
                    return " ".join([re.sub('<[^<]+?>', '', s) for s in snippets[:2]])
        except: return None
        return None

    def summarize(self, text):
        """Lightweight text summarizer"""
        sentences = text.split('.')
        if len(sentences) > 3:
            return ". ".join(sentences[:2]) + "... (Summary complete)."
        return text

    def respond(self, text, model_type):
        text_lower = text.lower()
        
        if model_type == "Pro":
            # Check for summarization request
            if "summarize" in text_lower:
                return f"📝 **Summary:** {self.summarize(text)}"
            
            # Logic for 'Who', 'What', 'How'
            search_triggers = ["who is", "who it", "what is", "how to", "tell me about"]
            if any(trigger in text_lower for trigger in search_triggers):
                data = self.search_web(text)
                if data:
                    return f"🔍 **Pro Research Insight:**\n\n{data}"

        # Standard Flash Logic
        return f"I analyzed your request: '{text}'. How can I help further?"

def check_rate_limit():
    """Real-time live countdown timer"""
    if "last_msg_time" not in st.session_state:
        st.session_state.last_msg_time = []
    
    now = time.time()
    st.session_state.last_msg_time.append(now)
    st.session_state.last_msg_time = [t for t in st.session_state.last_msg_time if now - t < 10]
    
    # Check if spamming
    if len(st.session_state.last_msg_time) > 4:
        st.session_state.suspended_until = now + 60
        timer_placeholder = st.empty()
        
        while time.time() < st.session_state.suspended_until:
            remaining = int(st.session_state.suspended_until - time.time())
            timer_placeholder.error(f"⚠️ **System Stress Detected!** Data center cooling down. Wait **{remaining} seconds**.")
            time.sleep(1) # Real-time update
        
        timer_placeholder.empty()
        st.session_state.last_msg_time = []
        return True
    return True

def main():
    st.title("🤖 SmartBot AI Pro")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "engine" not in st.session_state:
        st.session_state.engine = SmartEngine()

    model = st.sidebar.selectbox("Select Model", ["SmartBot Pro", "SmartBot Flash"])

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask Pro anything..."):
        if check_rate_limit():
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner(f"{model} is thinking..."):
                    model_type = "Pro" if "Pro" in model else "Flash"
                    response = st.session_state.engine.respond(user_input, model_type)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
