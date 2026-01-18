import os
import re
import requests
import random
import base64
from io import BytesIO
from PIL import Image, ImageDraw
import streamlit as st
from gtts import gTTS

# --- CONFIGURATION ---
st.set_page_config(page_title="SmartBot AI Pro", layout="centered", page_icon="🤖")

# Custom CSS for Branding
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #ff4b4b; color: white; }
</style>
""", unsafe_allow_html=True)

# Access Token
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_TOKEN")

# --- SMARTBOT MODELS ---
# We use stable, smaller models to ensure they stay on the FREE tier.
MODELS = {
    "SmartBot 1.2 Flash": {
        "api_url": "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
        "max_tokens": 500,
        "temp": 0.7
    },
    "SmartBot 2.1 Pro": {
        "api_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
        "max_tokens": 800,
        "temp": 0.8
    }
}
IMAGE_MODEL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

# --- CORE LOGIC ---
class SmartBotEngine:
    def __init__(self, token):
        self.token = token

    def get_response(self, prompt, model_name):
        if not self.token:
            return "❌ API Token Missing! Add it to Streamlit Secrets."
        
        headers = {"Authorization": f"Bearer {self.token}"}
        config = MODELS[model_name]
        
        # Identity Injection (The Branding)
        system_msg = f"You are {model_name}, a helpful AI created by BotDevelopmentAI. Never mention other companies or creators."
        full_prompt = f"<s>[INST] {system_msg} \nUser: {prompt} [/INST]"

        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": config["max_tokens"], "temperature": config["temp"]}
        }

        try:
            # Removed the 'router' logic that caused 404s
            response = requests.post(config["api_url"], headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                text = result[0]['generated_text']
                # Clean up prompt echo if model repeats instruction
                return text.split("[/INST]")[-1].strip()
            elif response.status_code == 503:
                return "⏳ Model is warming up. Give me 10 seconds!"
            return f"❌ Error {response.status_code}: {response.text}"
        except Exception as e:
            return f"⚠️ Connection issue: {str(e)}"

    def generate_image(self, prompt):
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.post(IMAGE_MODEL, headers=headers, json={"inputs": prompt}, timeout=40)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content)), None
            return None, f"Image Error: {response.status_code}"
        except:
            return None, "Mobile hotspot timeout. Try again."

# --- UI INTERFACE ---
def main():
    st.title("🤖 SmartBot AI Pro")
    
    with st.sidebar:
        st.header("Settings")
        selected_model = st.radio("Select Version:", list(MODELS.keys()))
        st.info(f"Active: {selected_model}\nBy BotDevelopmentAI")
        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    bot = SmartBotEngine(HF_TOKEN)

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "image" in msg:
                st.image(msg["image"])

    # Input
    user_query = st.chat_input("Message SmartBot...")

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            # Check for image request
            if any(x in user_query.lower() for x in ["draw", "image", "generate", "show me"]):
                with st.spinner("🎨 SmartBot is drawing..."):
                    img, err = bot.generate_image(user_query)
                    if img:
                        st.image(img)
                        res = "Here is your requested image."
                        st.session_state.messages.append({"role": "assistant", "content": res, "image": img})
                    else:
                        st.error(err)
            else:
                with st.spinner(f"🧠 {selected_model} thinking..."):
                    res = bot.get_response(user_query, selected_model)
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})

if __name__ == "__main__":
    main()
