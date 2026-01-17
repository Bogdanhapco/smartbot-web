import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import streamlit as st

# --- UI CONFIG ---
st.set_page_config(page_title="SmartBot Ludy 1.2 Pro", layout="centered", page_icon="🤖")

# --- KNOWLEDGE & REASONING ENGINE ---
class LudyBrain:
    def __init__(self):
        self.context = []
        self.romanian_keywords = ["ce", "cine", "cum", "unde", "este", "salut", "poti", "fa-mi", "scrie"]

    def get_lang(self, text):
        return "ro" if any(w in text.lower().split() for w in self.romanian_keywords) else "en"

    def search_and_reason(self, query, model):
        lang = self.get_lang(query)
        clean_q = re.sub(r'(generate|draw|search|imagine|arata-mi|fa-mi|ce este|cine e)', '', query.lower()).strip()
        
        try:
            # 1. Search Logic
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_q.replace(' ', '%20')}&format=json"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
                if not data['query']['search']: return None, None
                title = data['query']['search'][0]['title']
            
            # 2. Reasoning / Extraction
            sum_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title.replace(' ', '_')}&format=json"
            with urllib.request.urlopen(sum_url, timeout=5) as r:
                p_data = json.loads(r.read().decode())
                page = list(p_data['query']['pages'].values())[0]
                full_text = page.get('extract', "")
            
            # 3. Model Logic (Pro gets more depth)
            sentences = re.split(r'(?<=[.!?]) +', full_text)
            limit = 8 if "Pro" in model else 3
            summary = " ".join(sentences[:limit])
            
            # Unique reasoning prefix
            reasoning = f"🤔 *Thinking: Analyzing the history and context of {title}...*" if lang == "en" else f"🤔 *Gândire: Analizez istoria și contextul pentru {title}...*"
            return f"{reasoning}\n\n{summary}", title
        except:
            return None, None

    def respond(self, prompt, model):
        lang = self.get_lang(prompt)
        p = prompt.lower()

        # Conversational Intelligence
        if any(w in p for w in ["hello", "hi", "salut", "buna"]):
            return "Hello! I'm Ludy. I can help you research topics or generate high-detail art. What's on your mind?" if lang == "en" else "Salut! Sunt Ludy. Te pot ajuta cu cercetări sau artă detaliată. La ce te gândești?"
        
        if any(w in p for w in ["how are you", "ce faci", "cum esti"]):
            return "I'm functioning at 100% capacity! Ready to create." if lang == "en" else "Funcționez la capacitate maximă! Sunt gata să creez."

        # Search/Reasoning Trigger
        answer, topic = self.search_and_reason(prompt, model)
        if answer:
            return answer
        
        return "I'm here to talk! If you want me to draw something, just use words like 'draw' or 'imagine'." if lang == "en" else "Sunt aici să vorbim! Dacă vrei să desenez ceva, folosește cuvinte precum 'desenează' sau 'imaginează'."

# --- ADVANCED TEXTURE RENDERER ---
class LudyRenderer:
    def __init__(self, style):
        self.style = style

    def create_noise_texture(self, size, color1, color2, scale=10):
        """Creates an organic texture using noise layers."""
        base = Image.new('RGB', size, color1)
        draw = ImageDraw.Draw(base)
        for _ in range(2000):
            x, y = random.randint(0, size[0]-1), random.randint(0, size[1]-1)
            draw.point((x, y), fill=color2)
        return base.filter(ImageFilter.GaussianBlur(radius=2))

    def draw_detailed_house(self, draw, x, y, size):
        # Brick Texture for walls
        for j in range(y, y + size):
            for i in range(x, x + size):
                if (i // 10 + j // 5) % 2 == 0:
                    draw.point((i, j), fill=(160, 60, 50)) # Brick red
                else:
                    draw.point((i, j), fill=(140, 50, 40)) # Mortar/Shadow
        # Wood texture for door
        draw.rectangle([x+size//3, y+size//2, x+2*size//3, y+size], fill=(101, 67, 33))
        # Glass window with reflection
        draw.rectangle([x+size//10, y+size//10, x+size//3, y+size//3], fill=(135, 206, 235))
        draw.line([x+size//10, y+size//10, x+size//3, y+size//3], fill="white", width=1)

    def generate(self, prompt, model):
        res = 1024 if "Pro" in model else 512
        img = Image.new('RGB', (res, res), (30, 30, 40))
        draw = ImageDraw.Draw(img)
        p = prompt.lower()

        # 1. Background with Real Textures
        sky_tex = self.create_noise_texture((res, res//2), (100, 150, 255), (255, 255, 255))
        img.paste(sky_tex, (0, 0))
        
        ground_color = (34, 139, 34) if "grass" in p or "forest" in p else (100, 100, 100)
        ground_tex = self.create_noise_texture((res, res//2), ground_color, (20, 50, 20))
        img.paste(ground_tex, (0, res//2))

        # 2. Detailed Objects
        if "house" in p:
            self.draw_detailed_house(draw, res//4, res//2-100, 200)
        
        if "mountain" in p:
            draw.polygon([(0, res//2), (res//2, res//6), (res, res//2)], fill=(80, 80, 90))
            # Add snow cap with texture
            draw.polygon([(res//2-50, res//4), (res//2, res//6), (res//2+50, res//4)], fill=(240, 240, 255))

        # 3. Post-Processing (Realism)
        if self.style == "Cinematic":
            img = ImageEnhance.Contrast(img).enhance(1.4)
            img = ImageEnhance.Color(img).enhance(1.2)
        elif self.style == "Cyberpunk":
            img = ImageOps.colorize(img.convert("L"), black="blue", white="magenta")
        
        # Watermark
        draw = ImageDraw.Draw(img)
        draw.text((20, res-40), "Generated with Ludy 1.2 Pro Engine", fill=(255,255,255,128))
        return img

# --- STREAMLIT APP LOGIC ---
with st.sidebar:
    st.header("Ludy Core Settings")
    model_choice = st.selectbox("Engine", ["Ludy 1.1 Flash", "Ludy 1.2 Pro"])
    style_choice = st.selectbox("Artistic Texture", ["Realistic", "Cinematic", "Cyberpunk", "Oil Painting"])
    st.info("Pro Engine uses Deep Reasoning and 1024px Textures.")

st.title(f"🤖 {model_choice}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "brain" not in st.session_state:
    st.session_state.brain = LudyBrain()

# History Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg: st.image(msg["image"])

# Input Logic
if prompt := st.chat_input("Talk to Ludy or ask for a drawing..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # IMAGE PATH
    if any(x in prompt.lower() for x in ["draw", "generate", "picture", "imagine", "arata-mi"]):
        with st.chat_message("assistant"):
            st.write("🌌 *Initializing Latent Texture Mapping...*")
            prog = st.progress(0)
            placeholder = st.empty()
            
            renderer = LudyRenderer(style_choice)
            final_img = renderer.generate(prompt, model_choice)
            
            # Diffusion Effect
            steps = 15 if "Pro" in model_choice else 6
            for i in range(steps + 1):
                noise_lvl = (steps - i) * 4
                temp = final_img.filter(ImageFilter.GaussianBlur(radius=noise_lvl))
                placeholder.image(temp, caption=f"Denoising Step {i}/{steps}")
                prog.progress(i/steps)
                time.sleep(0.1)
            
            st.session_state.messages.append({"role": "assistant", "content": "I've rendered this with high-detail textures for you.", "image": final_img})
    
    # CHAT PATH
    else:
        with st.chat_message("assistant"):
            response = st.session_state.brain.respond(prompt, model_choice)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
