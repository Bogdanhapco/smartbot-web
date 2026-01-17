import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from gtts import gTTS
import streamlit as st

# --- CONFIGURATION ---
st.set_page_config(page_title="SmartBot AI - Ludy Engine", layout="centered", page_icon="🤖")

# --- VOICE ENGINE ---
def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("speech.mp3")
        return "speech.mp3"
    except:
        return None

# --- SMARTBOT BRAIN (Reasoning & Web) ---
class SmartBotBrain:
    def __init__(self):
        self.history = []

    def search_web(self, query, model):
        clean_q = re.sub(r'(generate|draw|search|imagine|arata-mi|fa-mi|ce este|cine e)', '', query.lower()).strip()
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_q.replace(' ', '%20')}&format=json"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
                if not data['query']['search']: return None, None
                title = data['query']['search'][0]['title']
            
            sum_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title.replace(' ', '_')}&format=json"
            with urllib.request.urlopen(sum_url, timeout=5) as r:
                p_data = json.loads(r.read().decode())
                page = list(p_data['query']['pages'].values())[0]
                return page.get('extract', ""), title
        except: return None, None

    def reason_and_respond(self, prompt, model):
        # Personality Guard
        if "who are you" in prompt.lower():
            return "I am SmartBot. My creative heart is the Ludy Image Engine."
        
        # Web Search & Reasoning Step
        info, title = self.search_web(prompt, model)
        if info:
            reasoning = f"**Reasoning Steps:**\n1. Identified core topic: '{title}'\n2. Scanning global knowledge base...\n3. Synthesizing unique summary for {model} mode."
            summary = " ".join(re.split(r'(?<=[.!?]) +', info)[:5 if "Pro" in model else 2])
            return f"{reasoning}\n\n**SmartBot Answer:** {summary}"
        
        return "I'm processing that as a conversational request. Let's talk!"

# --- LUDY IMAGE GENERATOR (Textured Rendering) ---
class LudyGenerator:
    def __init__(self, style):
        self.style = style

    def apply_textures(self, draw, x, y, w, h, base_color, type="wood"):
        for i in range(h):
            for j in range(w):
                noise = random.randint(-15, 15)
                r = max(0, min(255, base_color[0] + noise))
                g = max(0, min(255, base_color[1] + noise))
                b = max(0, min(255, base_color[2] + noise))
                if type == "brick" and (i % 5 == 0 or j % 15 == 0): # Brick lines
                    draw.point((x+j, y+i), fill=(80, 80, 80))
                else:
                    draw.point((x+j, y+i), fill=(r, g, b))

    def generate(self, prompt, model):
        res = 1024 if "Pro" in model else 512
        img = Image.new('RGB', (res, res), (30, 30, 35))
        draw = ImageDraw.Draw(img)
        p = prompt.lower()

        # Backgrounds
        draw.rectangle([0, 0, res, res//2], fill=(135, 206, 235) if "night" not in p else (10, 10, 30))
        draw.rectangle([0, res//2, res, res], fill=(34, 139, 34)) # Grass

        # Object: Textured House
        if "house" in p:
            # Wall
            self.apply_textures(draw, res//4, res//2-100, 200, 100, (150, 75, 0), "wood")
            # Roof
            draw.polygon([(res//4-20, res//2-100), (res//4+100, res//2-180), (res//4+220, res//2-100)], fill=(100, 40, 40))
        
        # Object: Car
        if "car" in p:
            draw.rectangle([res//2, res-120, res//2+150, res-70], fill="red", outline="black")
            draw.ellipse([res//2+10, res-80, res//2+40, res-50], fill="black")
            draw.ellipse([res//2+100, res-80, res//2+130, res-50], fill="black")

        # Post-Processing
        if self.style == "Cinematic": img = ImageEnhance.Contrast(img).enhance(1.6)
        
        # Watermark
        draw.text((20, res-40), "Generated with Ludy 1.2 Texture-Engine", fill=(255, 255, 255))
        return img

# --- UI LAYOUT ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=80)
    st.title("SmartBot Control")
    model_choice = st.selectbox("Intelligence Level", ["SmartBot Flash", "SmartBot Pro"])
    style_choice = st.selectbox("Ludy Style", ["Photorealistic", "Cinematic", "Cyberpunk", "Oil Painting"])
    use_voice = st.checkbox("Enable Voice Responses", value=True)

st.title(f"🤖 {model_choice}")

if "messages" not in st.session_state: st.session_state.messages = []
if "brain" not in st.session_state: st.session_state.brain = SmartBotBrain()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("Talk to SmartBot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # IMAGE LOGIC
        if any(x in prompt.lower() for x in ["draw", "generate", "image", "picture"]):
            st.write("Ludy Generator is texturing the canvas...")
            ludy = LudyGenerator(style_choice)
            final_img = ludy.generate(prompt, model_choice)
            
            # Diffusion Effect
            placeholder = st.empty()
            for i in range(10):
                blur = (10 - i) * 2
                placeholder.image(final_img.filter(ImageFilter.GaussianBlur(radius=blur)))
                time.sleep(0.1)
            
            st.session_state.messages.append({"role": "assistant", "content": "Created with Ludy Engine.", "image": final_img})
        
        # CHAT LOGIC
        else:
            response = st.session_state.brain.reason_and_respond(prompt, model_choice)
            st.markdown(response)
            
            if use_voice:
                audio_path = speak_text(response.split("SmartBot Answer:")[-1])
                if audio_path: st.audio(audio_path)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
