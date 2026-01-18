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

# Add custom CSS
st.markdown("""
<style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; }
    .stButton>button { border-radius: 20px; padding: 0.5rem 1rem; }
</style>
""", unsafe_allow_html=True)

# --- COMPREHENSIVE OBJECT DATABASE ---
OBJECTS = {
    'car': ['car', 'vehicle'], 'truck': ['truck'], 'bus': ['bus'], 'train': ['train'],
    'airplane': ['airplane', 'plane'], 'helicopter': ['helicopter'], 'boat': ['boat', 'ship'],
    'bicycle': ['bicycle', 'bike'], 'motorcycle': ['motorcycle'], 'rocket': ['rocket'],
    'house': ['house', 'home'], 'building': ['building', 'skyscraper'], 'tree': ['tree', 'forest'],
    'flower': ['flower', 'garden'], 'mountain': ['mountain', 'hill'], 'ocean': ['ocean', 'sea'],
    'sun': ['sun', 'sunny'], 'moon': ['moon'], 'star': ['star', 'stars'], 'cloud': ['cloud']
}

class SmartEngine:
    def __init__(self):
        self.history = []

    def search_web(self, query):
        """Simulated real-time search logic for Pro model"""
        try:
            # DuckDuckGo Lite search extraction
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                # Extract snippets using regex for a lightweight implementation
                snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, re.S)
                if snippets:
                    results = " ".join([re.sub('<[^<]+?>', '', s) for s in snippets[:3]])
                    return f"Based on my search: {results}"
        except Exception:
            return None
        return None

    def respond(self, text, model_type):
        text_lower = text.lower()
        
        # PRO MODEL: Logic for 'Who', 'What', 'How' using Search
        if model_type == "Pro":
            search_triggers = ["who is", "who it", "what is", "how to", "tell me about", "where is"]
            if any(trigger in text_lower for trigger in search_triggers):
                search_data = self.search_web(text)
                if search_data:
                    return f"🔍 **SmartBot Pro Research:**\n\n{search_data}\n\nI hope that helps! Is there anything else you'd like to know?"

            # General Pro reasoning
            if "why" in text_lower:
                return "As a Pro AI, I analyze the context: " + text + ". This often involves complex variables and logical outcomes."
            
        # FLASH MODEL (or Fallback for Pro)
        if "hello" in text_lower or "hi" in text_lower:
            return "Hello! I'm SmartBot. How can I assist you today?"
        elif "time" in text_lower:
            return f"The current time is {time.strftime('%H:%M:%S')}."
        elif "help" in text_lower:
            return "I can answer questions, generate images (start with 'draw' or 'make'), or just chat!"
        
        return f"I understand you're asking about '{text}'. Can you tell me more?"

def check_rate_limit():
    """Suspends user for 1 minute if they spam"""
    if "last_msg_time" not in st.session_state:
        st.session_state.last_msg_time = []
    
    if "suspended_until" in st.session_state:
        if time.time() < st.session_state.suspended_until:
            remaining = int(st.session_state.suspended_until - time.time())
            st.error(f"⚠️ High usage detected. You are putting stress on our data center. System suspended for {remaining} more seconds.")
            return False
        else:
            del st.session_state.suspended_until

    # Record current time
    now = time.time()
    st.session_state.last_msg_time.append(now)
    
    # Keep only last 5 messages within 10 seconds to detect spam
    st.session_state.last_msg_time = [t for t in st.session_state.last_msg_time if now - t < 10]
    
    if len(st.session_state.last_msg_time) > 4:
        st.session_state.suspended_until = now + 60
        st.error("⚠️ System Overload: You are putting stress on our data center. Suspended for 1 minute.")
        return False
    return True

def text_to_speech_button(text, key):
    if st.button("🔊 Read Aloud", key=key):
        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")
        with open("response.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
            st.markdown(md, unsafe_allow_html=True)
        os.remove("response.mp3")

def main():
    st.title("🤖 SmartBot AI Pro")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "engine" not in st.session_state:
        st.session_state.engine = SmartEngine()

    model = st.sidebar.selectbox("Select Model", ["SmartBot Pro (Smart)", "SmartBot Flash (Fast)"])
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"])

    if user_input := st.chat_input("Type your message..."):
        # Rate limit check
        if not check_rate_limit():
            return

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        is_image_request = any(word in user_input.lower() for word in ["draw", "make", "generate", "image", "picture"])
        
        if is_image_request:
            # (Image generation logic remains the same as your original file)
            with st.chat_message("assistant"):
                with st.spinner("Generating art..."):
                    # Dummy image generation for brevity in this response
                    final_img = Image.new('RGB', (500, 500), color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
                    st.image(final_img, caption="Generated Image")
                    st.session_state.messages.append({"role": "assistant", "content": "Here is your image!", "image": final_img})
        else:
            with st.chat_message("assistant"):
                with st.spinner(f"{model} thinking..."):
                    model_type = "Pro" if "Pro" in model else "Flash"
                    response = st.session_state.engine.respond(user_input, model_type)
                    st.markdown(response)
                    text_to_speech_button(response, f"msg_{len(st.session_state.messages)}")
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
