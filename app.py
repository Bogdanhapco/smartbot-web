import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter
import streamlit as st

# --- CONFIGURATION & UI ---
st.set_page_config(page_title="SmartBot AI", layout="centered")

# --- KNOWLEDGE & CHAT ENGINE (Conversational) ---
class SmartChatEngine:
    def __init__(self):
        self.context = []  # Stores recent topics for context
        self.cache = {}
    
    def update_context(self, text):
        # Extract potential nouns/topics to remember context
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        if words:
            self.context = (words + self.context)[:5]

    def get_context_hint(self):
        return self.context[0] if self.context else ""

    def search_wikipedia(self, query, model_type):
        # If query contains "it", "he", "she", try to use context
        if any(w in query.lower().split() for w in ["it", "he", "she", "that"]) and self.context:
            query = f"{self.context[0]} {query}"
        
        # Flash Model: Quick, short search
        # Pro Model: Detailed search
        sentences_to_fetch = 3 if model_type == "Flash" else 8
        
        try:
            # 1. Search for title
            search_term = query.replace(" ", "%20")
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
            
            with urllib.request.urlopen(search_url, timeout=3) as r:
                data = json.loads(r.read().decode())
                if not data['query']['search']:
                    return None
                best_title = data['query']['search'][0]['title']
                self.update_context(best_title)
            
            # 2. Get content
            content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles={best_title.replace(' ', '_')}&format=json&redirects=1"
            with urllib.request.urlopen(content_url, timeout=3) as r:
                data = json.loads(r.read().decode())
                page = list(data['query']['pages'].values())[0]
                text = page.get('extract', "")
                
                # Split into sentences and truncate
                sentences = re.split(r'(?<=[.!?]) +', text)
                summary = " ".join(sentences[:sentences_to_fetch])
                return summary, best_title
                
        except:
            return None, None

    def respond(self, user_input, model_type):
        user_input_lower = user_input.lower()
        
        # 1. Small Talk / Personality (No internet needed)
        greetings = ["hello", "hi", "hey", "sup"]
        if any(w in user_input_lower for w in greetings):
            return f"Hello! I am SmartBot {model_type}. Ready to help!"
        
        if "who are you" in user_input_lower:
            return "I am SmartBot, a lightweight AI designed for reasoning and image generation."

        # 2. Reasoning / Knowledge Lookup
        summary, topic = self.search_wikipedia(user_input, model_type)
        
        if summary:
            if model_type == "Pro":
                return f"**Analysis of {topic}:**\n\n{summary}\n\n*Refined based on Pro Logic.*"
            else:
                return f"Here is what I found about **{topic}**: {summary}"
        
        # 3. Fallback
        return "I'm not sure about that yet. I'm learning! Try asking about a specific topic, object, or place."

# --- PROMPT PARSER (Spatial Understanding) ---
class PromptParser:
    def __init__(self):
        self.objects = {
            'car': ['car', 'vehicle', 'automobile'], 'house': ['house', 'home', 'building'],
            'tree': ['tree', 'forest'], 'person': ['person', 'human', 'man', 'woman'],
            'sun': ['sun'], 'moon': ['moon'], 'mountain': ['mountain'],
            'cloud': ['cloud'], 'bird': ['bird'], 'flower': ['flower'],
            'road': ['road', 'street'], 'water': ['water', 'lake', 'river', 'ocean'],
            'boat': ['boat', 'ship'], 'city': ['city', 'skyline'],
            'dog': ['dog', 'puppy'], 'cat': ['cat', 'kitten'],
            'star': ['star'], 'grass': ['grass', 'field'],
            'airplane': ['airplane', 'plane']
        }
        self.colors = {'red':['red'], 'blue':['blue'], 'green':['green'], 'yellow':['yellow'], 'orange':['orange'], 'purple':['purple'], 'black':['black'], 'white':['white'], 'brown':['brown']}
        self.times = {'day':['day'], 'night':['night'], 'sunset':['sunset'], 'sunrise':['sunrise']}
        self.weather = {'sunny':['sunny'], 'rainy':['rain'], 'snowy':['snow'], 'cloudy':['cloud']}
    
    def parse(self, prompt):
        p = prompt.lower()
        scene = {'objects':[], 'colors':[], 'time':'day', 'weather':'sunny', 'relationships':[]}
        
        for obj, kws in self.objects.items():
            if any(k in p for k in kws): scene['objects'].append(obj)
        for col, kws in self.colors.items():
            if any(k in p for k in kws): scene['colors'].append(col)
        for t, kws in self.times.items():
            if any(k in p for k in kws): scene['time'] = t
        for w, kws in self.weather.items():
            if any(k in p for k in kws): scene['weather'] = w
            
        # Default objects if empty
        if not scene['objects']: scene['objects'] = ['tree', 'mountain', 'cloud']
        return scene

# --- RENDERER (The Painting Engine) ---
class AdvancedRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def perlin(self, x, y, scale=50):
        # Simplified pseudo-noise
        return (math.sin(x/scale) + math.cos(y/scale) + math.sin((x+y)/scale))/3

    def get_color(self, base, variance=20):
        r, g, b = base
        v = random.randint(-variance, variance)
        return (max(0, min(255, r+v)), max(0, min(255, g+v)), max(0, min(255, b+v)))

    def render(self, scene):
        img = Image.new('RGB', (self.width, self.height), 'black')
        draw = ImageDraw.Draw(img)
        
        # 1. Background (Sky/Ground)
        time = scene['time']
        sky_col = (135, 206, 235) if time == 'day' else (10, 10, 30)
        if time == 'sunset': sky_col = (255, 140, 0)
        draw.rectangle((0, 0, self.width, self.height), fill=sky_col)
        
        g_col = (34, 139, 34) if time != 'snowy' else (240, 248, 255)
        draw.rectangle((0, self.height//2, self.width, self.height), fill=g_col)

        # 2. Procedural Elements
        objs = scene['objects']
        
        if 'mountain' in objs:
            pts = [(0, 300), (150, 100), (300, 300), (450, 150), (600, 300)]
            draw.polygon(pts, fill=(105, 105, 105), outline='black')
            # Snow caps
            draw.polygon([(150,100), (120,160), (180,160)], fill='white')
            
        if 'water' in objs:
            draw.rectangle((0, 350, self.width, self.height), fill=(65, 105, 225))

        if 'road' in objs:
            # Perspective road
            draw.polygon([(250, 300), (350, 300), (500, self.height), (100, self.height)], fill=(50, 50, 50))
            draw.line((300, 300, 300, self.height), fill='yellow', width=2)

        if 'tree' in objs:
            for x in [50, 550]:
                draw.rectangle((x, 250, x+20, 350), fill=(139, 69, 19))
                draw.ellipse((x-20, 200, x+40, 260), fill=(0, 100, 0))

        if 'house' in objs:
            h_col = (200, 50, 50) if 'red' in scene['colors'] else (139, 69, 19)
            draw.rectangle((200, 250, 350, 350), fill=h_col, outline='black')
            draw.polygon([(190, 250), (360, 250), (275, 180)], fill=(50, 50, 50), outline='black')
            draw.rectangle((260, 300, 290, 350), fill=(100, 50, 0)) # Door

        if 'car' in objs:
            c_col = (255, 0, 0) if 'red' in scene['colors'] else (0, 0, 255)
            draw.rectangle((300, 320, 400, 350), fill=c_col) # Body
            draw.rectangle((320, 300, 380, 320), fill=(200, 200, 200)) # Top
            draw.ellipse((310, 340, 330, 360), fill='black') # Wheel
            draw.ellipse((370, 340, 390, 360), fill='black') # Wheel

        if 'sun' in objs or time == 'day':
            draw.ellipse((450, 50, 530, 130), fill='yellow')
        
        if 'moon' in objs or time == 'night':
            draw.ellipse((450, 50, 500, 100), fill='white')

        return img

# --- APP LOGIC ---

# 1. Sidebar Control
with st.sidebar:
    st.header("⚙️ Model Configuration")
    model_version = st.radio(
        "Select Model Version:",
        ("SmartBot 1.1 Flash", "SmartBot 1.2 Pro"),
        index=1
    )
    
    st.markdown("---")
    st.markdown("**Model Stats:**")
    if model_version == "SmartBot 1.1 Flash":
        st.markdown("🚀 **Speed:** Extreme")
        st.markdown("🧠 **Reasoning:** Basic")
        st.markdown("🎨 **Image Gen:** Fast Render")
    else:
        st.markdown("🚀 **Speed:** Standard")
        st.markdown("🧠 **Reasoning:** Advanced")
        st.markdown("🎨 **Image Gen:** Diffusion-Style")

# 2. Header
st.title("🤖 SmartBot AI")
st.caption(f"Running on {model_version} | Lightweight Diffusion & Reasoning Engine")

# 3. Initialize Session
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'bot_engine' not in st.session_state:
    st.session_state.bot_engine = SmartChatEngine()

# 4. Display Chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "image" in msg:
            st.image(msg["image"], caption="Generated by SmartBot Vision")

# 5. Handle Input
user_input = st.chat_input("Type a message or ask to generate an image...")

if user_input:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # PROCESS REQUEST
    query_lower = user_input.lower()
    img_triggers = ["generate", "draw", "create image", "paint", "show me"]
    is_image_req = any(t in query_lower for t in img_triggers)

    if is_image_req:
        # --- IMAGE GENERATION PIPELINE ---
        parser = PromptParser()
        scene = parser.parse(user_input)
        
        # Set resolution based on Model
        if model_version == "SmartBot 1.2 Pro":
            res_w, res_h = 1024, 768
            steps = 20 # More steps for "Pro" feel
        else:
            res_w, res_h = 512, 384
            steps = 5

        renderer = AdvancedRenderer(res_w, res_h)
        final_img = renderer.render(scene)
        
        # SIMULATE DIFFUSION PROCESS (Visual Effect)
        placeholder = st.empty()
        loading_bar = st.progress(0)
        
        with st.chat_message("assistant"):
            st.write(f"🎨 **Generating:** {', '.join(scene['objects'])} in {scene['time']} light...")
            
            # This loop simulates the "Denoising" look of diffusion
            for i in range(steps):
                # Create noise
                noise_level = 1.0 - (i / steps)
                noisy_img = final_img.copy()
                
                # Add noise filter logic
                noise_layer = Image.effect_noise((res_w, res_h), sigma=noise_level*100)
                noisy_img = Image.blend(noisy_img, noise_layer.convert("RGB"), alpha=noise_level)
                
                placeholder.image(noisy_img, caption=f"Step {i+1}/{steps} (Denoising...)")
                loading_bar.progress((i + 1) / steps)
                time.sleep(0.05 if model_version == "Flash" else 0.15)
            
            # Show Final
            placeholder.image(final_img, caption=f"Finished | {model_version}")
            loading_bar.empty()
            
            # Save to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Here is your image based on: '{user_input}'",
                "image": final_img
            })

    else:
        # --- CHAT PIPELINE ---
        with st.chat_message("assistant"):
            with st.spinner(f"{model_version} is thinking..."):
                response_text = st.session_state.bot_engine.respond(
                    user_input, 
                    "Pro" if "Pro" in model_version else "Flash"
                )
                st.write(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
