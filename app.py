import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import streamlit as st

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="SmartBot AI - Ludy Engine", layout="centered", page_icon="🤖")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; }
    .stProgress > div > div > div > div { background-color: #7000ff; }
    .stSidebar { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- REASONING & WEB ENGINE ---
class LudyBrain:
    def __init__(self):
        self.romanian_keywords = ["ce", "cine", "cum", "unde", "este", "salut", "poti", "fa-mi", "scrie", "ajutor"]
    
    def get_lang(self, text):
        return "ro" if any(w in text.lower().split() for w in self.romanian_keywords) else "en"

    def search_knowledge(self, query):
        # Cleaning prompt for search
        clean_q = re.sub(r'(generate|draw|search|imagine|arata-mi|fa-mi|ce este|cine e)', '', query.lower()).strip()
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_q.replace(' ', '%20')}&format=json"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
                if not data['query']['search']: return None
                title = data['query']['search'][0]['title']
            
            sum_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title.replace(' ', '_')}&format=json"
            with urllib.request.urlopen(sum_url, timeout=5) as r:
                p_data = json.loads(r.read().decode())
                page = list(p_data['query']['pages'].values())[0]
                return page.get('extract', "")
        except: return None

    def get_response(self, prompt, model):
        lang = self.get_lang(prompt)
        
        # Guardrail: No Coding
        if any(w in prompt.lower() for w in ["python", "code", "script", "html", "css", "program", "java"]):
            return "I am a creative AI designed for chat and images, I don't write code yet!" if lang == "en" else "Sunt un AI creativ pentru chat și imagini, nu scriu cod încă!"

        # Basic Chat & Web Logic
        if any(w in prompt.lower() for w in ["hello", "hi", "salut", "buna"]):
            return f"Hello! Ludy {model} here. Ready to create?" if lang == "en" else f"Salut! Sunt Ludy {model}. Ești gata să creăm ceva?"

        info = self.search_knowledge(prompt)
        if info:
            prefix = "According to my database: " if lang == "en" else "Conform bazei mele de date: "
            return prefix + info[:500] + "..."
            
        return "I'm processing your request. Could you be more specific?" if lang == "en" else "Procesez cererea ta. Poți fi mai specific?"

# --- IMAGE ENGINE (LUDY 1.1) ---
class LudyRenderer:
    def __init__(self, style):
        self.style = style

    def apply_style(self, img):
        if self.style == "Cinematic":
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = ImageEnhance.Color(img).enhance(1.2)
        elif self.style == "Oil Painting":
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img = ImageEnhance.Color(img).enhance(1.4)
        elif self.style == "Sketch":
            img = img.convert("L").filter(ImageFilter.CONTOUR)
        elif self.style == "Cyberpunk":
            # Add a neon tint
            overlay = Image.new('RGB', img.size, (255, 0, 255)) # Pink
            img = Image.blend(img, overlay, 0.15)
            img = ImageEnhance.Contrast(img).enhance(1.8)
        return img

    def add_watermark(self, img):
        draw = ImageDraw.Draw(img)
        w, h = img.size
        # Bottom bar
        draw.rectangle([0, h-40, w, h], fill=(0, 0, 0, 180))
        draw.text((20, h-30), "Generated with Ludy 1.1", fill=(255, 255, 255))
        return img

    def generate(self, prompt, model):
        # Base colors
        res = 1024 if "Pro" in model else 512
        img = Image.new('RGB', (res, res), (30, 30, 40))
        draw = ImageDraw.Draw(img)
        p = prompt.lower()

        # Simple Procedural Shapes
        # Sky/Ground
        sky = (135, 206, 235) if "day" in p else (10, 10, 30)
        draw.rectangle([0, 0, res, res//2], fill=sky)
        draw.rectangle([0, res//2, res, res], fill=(50, 80, 50) if "forest" in p else (40, 40, 40))
        
        # Objects
        if "mountain" in p: draw.polygon([(0, res//2), (res//2, res//4), (res, res//2)], fill=(100, 100, 110))
        if "sun" in p: draw.ellipse([res-150, 50, res-50, 150], fill="yellow")
        if "car" in p: draw.rectangle([res//3, res-200, res//3+200, res-120], fill="red")
        
        img = self.apply_style(img)
        return self.add_watermark(img)

# --- APP LAYOUT ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("Ludy Pro Dashboard")
    model_choice = st.selectbox("Engine", ["SmartBot 1.1 Flash", "SmartBot 1.2 Pro"])
    style_choice = st.selectbox("Art Style", ["Realistic", "Cinematic", "Cyberpunk", "Oil Painting", "Sketch"])
    st.divider()
    st.caption("© 2026 SmartBot AI Inc. | Ludy v1.1.2")

st.title(f"🤖 {model_choice}")
st.write(f"Current Style: **{style_choice}**")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "brain" not in st.session_state:
    st.session_state.brain = LudyBrain()

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg: st.image(msg["image"])

# User Input
if prompt := st.chat_input("Ask Ludy to draw or search..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    # IMAGE GENERATION TRIGGER
    if any(x in prompt.lower() for x in ["generate", "draw", "imagine", "arata-mi", "fa-mi"]):
        with st.chat_message("assistant"):
            st.write("Initializing Latent Diffusion Space...")
            progress = st.progress(0)
            img_placeholder = st.empty()
            
            renderer = LudyRenderer(style_choice)
            final_img = renderer.generate(prompt, model_choice)
            
            # THE DIFFUSION EFFECT (Blur to Clear)
            steps = 12 if "Pro" in model_choice else 6
            for i in range(steps + 1):
                blur_val = (steps - i) * 3
                # Create blurry version
                temp_img = final_img.filter(ImageFilter.GaussianBlur(radius=blur_val))
                # Add "noise" dots
                if i < steps/2:
                    d = ImageDraw.Draw(temp_img)
                    for _ in range(500): d.point([random.randint(0, final_img.width), random.randint(0, final_img.height)], fill="white")
                
                img_placeholder.image(temp_img, caption=f"Sampling: Step {i}/{steps}")
                progress.progress(i/steps)
                time.sleep(0.15)
            
            st.success("Rendering Complete.")
            st.session_state.messages.append({"role": "assistant", "content": "Here is your creation:", "image": final_img})
    
    # CHAT TRIGGER
    else:
        with st.chat_message("assistant"):
            resp = st.session_state.brain.get_response(prompt, model_choice)
            st.write(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})
