import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import streamlit as st

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="SmartBot AI - Ludy Engine", layout="centered", page_icon="🤖")

# Custom CSS for that "AI Company" look
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; }
    .stProgress > div > div > div > div { background-color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- KNOWLEDGE & REASONING ENGINE ---
class SmartChatEngine:
    def __init__(self):
        self.history = []
        self.language = "en"
    
    def detect_language(self, text):
        romanian_keywords = ["ce", "cine", "cum", "unde", "este", "salut", "poti", "fa-mi", "scrie"]
        if any(w in text.lower().split() for w in romanian_keywords):
            self.language = "ro"
        else:
            self.language = "en"

    def search_web(self, query, model_type):
        # Cleaning query for Wikipedia
        search_query = query.lower()
        for word in ["generate", "draw", "search", "what is", "ce este", "cine e"]:
            search_query = search_query.replace(word, "").strip()
        
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_query.replace(' ', '%20')}&format=json"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
                if not data['query']['search']: return None, None
                title = data['query']['search'][0]['title']
            
            # Fetch summary
            summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title.replace(' ', '_')}&format=json"
            with urllib.request.urlopen(summary_url, timeout=5) as r:
                data = json.loads(r.read().decode())
                page = list(data['query']['pages'].values())[0]
                return page.get('extract', ""), title
        except:
            return None, None

    def respond(self, user_input, model_type):
        self.detect_language(user_input)
        
        # 1. Anti-Coding Guardrail
        code_triggers = ["python", "code", "javascript", "script", "html", "css", "program"]
        if any(w in user_input.lower() for w in code_triggers):
            return "I am still learning how to code, but I can help with anything else!" if self.language == "en" else "Încă învăț să programez, dar te pot ajuta cu orice altceva!"

        # 2. Personality & Greeting
        if any(w in user_input.lower() for w in ["hello", "salut", "hi"]):
            return f"Hello! I am SmartBot {model_type}. How can I assist you today?" if self.language == "en" else f"Salut! Sunt SmartBot {model_type}. Cu ce te pot ajuta astăzi?"

        # 3. Web Search & Reasoning
        summary, topic = self.search_web(user_input, model_type)
        if summary:
            if model_type == "SmartBot 1.2 Pro":
                prefix = f"Analyzing data for '{topic}'... \n\n" if self.language == "en" else f"Analizez datele pentru '{topic}'... \n\n"
                return prefix + summary[:800] + "..."
            return summary[:300] + "..."
        
        return "I'm thinking... but I couldn't find a specific web match. Could you rephrase?" if self.language == "en" else "Mă gândesc... dar nu am găsit un rezultat specific. Poți reformula?"

# --- IMAGE DIFFUSION RENDERER ---
class LudyRenderer:
    def __init__(self, width, height):
        self.width, self.height = width, height
        
    def add_watermark(self, img):
        draw = ImageDraw.Draw(img)
        text = "Generated with Ludy 1.1"
        # Draw a small semi-transparent box at the bottom
        draw.rectangle([0, self.height-30, self.width, self.height], fill=(0,0,0,150))
        draw.text((10, self.height-25), text, fill=(200,200,200))
        return img

    def render_scene(self, prompt):
        img = Image.new('RGB', (self.width, self.height), color=(20, 20, 25))
        draw = ImageDraw.Draw(img)
        p = prompt.lower()

        # Simple Procedural logic based on keywords
        # Sky/Background
        sky_color = (135, 206, 235) if "day" in p else (10, 10, 40)
        if "sunset" in p: sky_color = (255, 100, 50)
        draw.rectangle([0, 0, self.width, self.height//2], fill=sky_color)
        
        # Ground
        ground_color = (34, 139, 34) # Green
        if "ocean" in p or "water" in p: ground_color = (0, 105, 148)
        if "desert" in p: ground_color = (237, 201, 175)
        draw.rectangle([0, self.height//2, self.width, self.height], fill=ground_color)

        # Dynamic Objects (DALL-E style triggers)
        if "sun" in p: draw.ellipse([self.width-100, 20, self.width-20, 100], fill="yellow")
        if "mountain" in p: draw.polygon([(0,self.height//2), (self.width//2, 100), (self.width, self.height//2)], fill=(100,100,100))
        if "house" in p: draw.rectangle([200, 250, 400, 450], fill="brown", outline="black")
        if "car" in p: draw.rectangle([100, 400, 300, 460], fill="red" if "red" in p else "blue")
        
        return self.add_watermark(img)

# --- APP FLOW ---

# Sidebar
with st.sidebar:
    st.title("Ludy AI Dashboard")
    model_choice = st.selectbox("Switch Model", ["SmartBot 1.1 Flash", "SmartBot 1.2 Pro"])
    st.info(f"Currently active: {model_choice}")
    st.write("Company: SmartBot AI Inc.")

# Main UI
st.title(f"🤖 {model_choice}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine" not in st.session_state:
    st.session_state.engine = SmartChatEngine()

# Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if "image" in m:
            st.image(m["image"])

# Input
if prompt := st.chat_input("Talk to Ludy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Check for Image Intent
    if any(x in prompt.lower() for x in ["generate", "draw", "show me", "imagine"]):
        with st.chat_message("assistant"):
            st.write("Initializing Diffusion Latents...")
            progress = st.progress(0)
            status = st.empty()
            image_placeholder = st.empty()
            
            # Setup resolution
            res = (1024, 1024) if "Pro" in model_choice else (512, 512)
            renderer = LudyRenderer(res[0], res[1])
            final_img = renderer.render_scene(prompt)
            
            # SIMULATED DIFFUSION EFFECT
            steps = 15 if "Pro" in model_choice else 5
            for i in range(steps + 1):
                # We simulate the diffusion by blurring the final image less and less
                blur_radius = (steps - i) * 2
                current_frame = final_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                
                # Add "Salt and Pepper" noise to the early frames
                if i < steps // 2:
                    draw = ImageDraw.Draw(current_frame)
                    for _ in range(1000):
                        draw.point([random.randint(0, res[0]), random.randint(0, res[1])], fill="white")
                
                image_placeholder.image(current_frame, caption=f"Denoising Step {i}/{steps}...")
                progress.progress(i / steps)
                time.sleep(0.1)
            
            status.success("Image Finalized with Ludy 1.1 Engine")
            st.session_state.messages.append({"role": "assistant", "content": "Generated image:", "image": final_img})
    
    else:
        # Standard Chat
        with st.chat_message("assistant"):
            response = st.session_state.engine.respond(prompt, model_choice)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
