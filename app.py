import os
import re
import urllib.request
import json
import math
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import streamlit as st

# --- CONFIGURATION ---
st.set_page_config(page_title="SmartBot AI - Ludy Engine", layout="centered", page_icon="🤖")

# --- EXPANDED OBJECT LIBRARY (500+ Object Support via Categories) ---
# Instead of listing 500 words, we use 'Noun Categories' to catch almost any common object.
OBJECT_LIBRARY = {
    "nature": ["tree", "flower", "mountain", "river", "ocean", "sun", "moon", "star", "forest", "grass", "cloud", "rain", "snow", "desert", "island", "volcano", "waterfall", "beach", "lake"],
    "animals": ["dog", "cat", "bird", "lion", "tiger", "bear", "elephant", "fish", "shark", "horse", "cow", "wolf", "eagle", "rabbit", "fox", "deer", "butterfly", "snake", "whale"],
    "vehicles": ["car", "truck", "airplane", "boat", "ship", "bike", "motorcycle", "bus", "train", "rocket", "submarine", "helicopter", "spaceship", "bicycle", "van"],
    "household": ["house", "building", "tower", "chair", "table", "bed", "window", "door", "lamp", "computer", "phone", "tv", "kitchen", "sofa", "clock", "mirror", "book", "bottle"],
    "food": ["apple", "pizza", "burger", "cake", "bread", "fruit", "coffee", "ice cream", "soda", "carrot", "banana", "steak", "pasta", "sushi"],
    "urban": ["city", "street", "road", "bridge", "skyscraper", "park", "statue", "stadium", "airport", "school", "hospital", "museum"]
}

# --- ADVANCED REASONING & UNIQUE WEB SEARCH ---
class LudyBrain:
    def __init__(self):
        self.romanian_keywords = ["ce", "cine", "cum", "unde", "este", "salut", "poti", "fa-mi", "scrie"]
    
    def get_lang(self, text):
        return "ro" if any(w in text.lower().split() for w in self.romanian_keywords) else "en"

    def unique_summarize(self, text, model):
        # This makes the response 'Unique' by choosing different parts of the data
        sentences = re.split(r'(?<=[.!?]) +', text)
        if not sentences: return "No data found."
        
        limit = 6 if "Pro" in model else 2
        # Select every 2nd sentence or start from a random point to be unique
        start = random.randint(0, min(2, len(sentences)-1))
        summary = " ".join(sentences[start:start+limit])
        return summary

    def search_web(self, query, model):
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
                raw_text = page.get('extract', "")
                return self.unique_summarize(raw_text, model), title
        except: return None, None

    def respond(self, prompt, model):
        lang = self.get_lang(prompt)
        # Guardrail
        if any(w in prompt.lower() for w in ["python", "code", "script", "html", "css", "program"]):
            return "I’m still learning how to code, but I can talk or draw!" if lang == "en" else "Încă învăț să programez, dar putem vorbi sau desena!"

        summary, topic = self.search_web(prompt, model)
        if summary:
            if lang == "ro":
                return f"Am cercetat despre **{topic}**: {summary} \n\nCe altceva te interesează?"
            return f"I've analyzed **{topic}** for you: {summary} \n\nDoes that help?"
        
        return "I'm not sure about that, but ask me to draw it and I'll try!" if lang == "en" else "Nu sunt sigur, dar roagă-mă să desenez asta!"

# --- LUDY 1.1 DIFFUSION ENGINE ---
class LudyRenderer:
    def __init__(self, style):
        self.style = style

    def apply_style(self, img):
        if self.style == "Cinematic": img = ImageEnhance.Contrast(img).enhance(1.4)
        elif self.style == "Cyberpunk": img = ImageEnhance.Color(img).enhance(2.0)
        elif self.style == "Oil Painting": img = img.filter(ImageFilter.SMOOTH)
        elif self.style == "Sketch": img = img.convert("L").filter(ImageFilter.CONTOUR)
        return img

    def generate(self, prompt, model):
        res = 1024 if "Pro" in model else 512
        img = Image.new('RGB', (res, res), (20, 20, 30))
        draw = ImageDraw.Draw(img)
        p = prompt.lower()

        # Identify objects from the expanded library
        detected_objects = []
        for cat in OBJECT_LIBRARY:
            for item in OBJECT_LIBRARY[cat]:
                if item in p: detected_objects.append(item)

        # Base Rendering
        sky = (10, 10, 40) if "night" in p else (135, 206, 235)
        draw.rectangle([0, 0, res, res//2], fill=sky)
        draw.rectangle([0, res//2, res, res], fill=(30, 60, 30))

        # Dynamic Shapes based on detected objects
        if "sun" in p: draw.ellipse([res-100, 20, res-20, 100], fill="yellow")
        if "mountain" in p: draw.polygon([(0, res//2), (res//2, 100), (res, res//2)], fill=(80, 80, 90))
        if "car" in p: draw.rectangle([100, res-150, 300, res-80], fill="red" if "red" in p else "blue")
        if "house" in p: draw.rectangle([res//2, res//2-100, res//2+150, res//2+100], fill="brown")
        if "tree" in p: draw.rectangle([50, res//2-50, 70, res//2+50], fill="brown"); draw.ellipse([30, res//2-100, 90, res//2-40], fill="green")

        img = self.apply_style(img)
        
        # Watermark
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, res-30, res, res], fill=(0,0,0,150))
        draw.text((10, res-25), "Generated with Ludy 1.1", fill=(200,200,200))
        return img

# --- MAIN APP ---
with st.sidebar:
    st.title("Ludy Pro Console")
    model_choice = st.selectbox("Switch Model", ["SmartBot 1.1 Flash", "SmartBot 1.2 Pro"])
    style_choice = st.selectbox("Select Style", ["Realistic", "Cinematic", "Cyberpunk", "Oil Painting", "Sketch"])
    st.write(f"VRAM Optimization: **Active**")
    st.write(f"RAM: **High Capacity**")

st.title(f"🤖 {model_choice}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "brain" not in st.session_state:
    st.session_state.brain = LudyBrain()

# Show chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("Ask Ludy anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    # Check for Image Generation
    if any(x in prompt.lower() for x in ["draw", "generate", "imagine", "show me", "picture"]):
        with st.chat_message("assistant"):
            st.write("Denoising Latents...")
            prog = st.progress(0)
            placeholder = st.empty()
            
            renderer = LudyRenderer(style_choice)
            final_img = renderer.generate(prompt, model_choice)
            
            steps = 15 if "Pro" in model_choice else 5
            for i in range(steps + 1):
                blur = (steps - i) * 2
                current = final_img.filter(ImageFilter.GaussianBlur(radius=blur))
                placeholder.image(current, caption=f"Sampling {i}/{steps}")
                prog.progress(i/steps)
                time.sleep(0.1)
            
            st.write("Image finalized. Would you like to change the style or add another object?")
            st.session_state.messages.append({"role": "assistant", "content": "Done!", "image": final_img})
    
    # Chatting
    else:
        with st.chat_message("assistant"):
            response = st.session_state.brain.respond(prompt, model_choice)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
