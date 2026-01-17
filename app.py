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
st.set_page_config(page_title="SmartBot AI", layout="centered", page_icon="🤖")

# --- DYNAMIC KNOWLEDGE & HUMAN-LIKE SUMMARY ---
class SmartBotBrain:
    def __init__(self):
        self.context_history = []

    def fetch_web_data(self, topic):
        try:
            # Clean the topic for Wikipedia
            clean_topic = re.sub(r'(who is|what is|tell me about|search for|define)', '', topic.lower()).strip()
            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={clean_topic.replace(' ', '%20')}&format=json&redirects=1"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
                pages = data.get('query', {}).get('pages', {})
                page = next(iter(pages.values()))
                return page.get('extract', "")
        except:
            return ""

    def human_summarize(self, text):
        if not text: return "I searched my database but couldn't find a clear answer. Should we try drawing it instead?"
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?]) +', text)
        
        # Pick 3-4 sentences but mix them up to sound "Unique" and human
        intro = ["So, basically, ", "Here's what I found: ", "Interestingly, ", "From what I can tell, "]
        summary = random.choice(intro) + " ".join(sentences[:3])
        
        if len(sentences) > 3:
            summary += f"\n\nBasically, the main thing to remember is {sentences[3 if len(sentences) > 3 else 0]}"
        
        return summary

    def get_response(self, prompt):
        # 1. Check if it's a question (Who is/What is/etc)
        if any(w in prompt.lower() for w in ["who is", "what is", "tell me about", "define", "how does"]):
            raw_data = self.fetch_web_data(prompt)
            human_answer = self.human_summarize(raw_data)
            return f"🔎 **SmartBot Search Result:**\n\n{human_answer}"
        
        # 2. Otherwise, talk normally
        responses = [
            "That's a great point! Tell me more.",
            "I see what you mean. I'm listening!",
            "Interesting... how does that make you feel?",
            "I'm here for it! What's our next move?"
        ]
        return random.choice(responses)

# --- LUDY GENERATOR (TEXTURE ENGINE) ---
class LudyGenerator:
    def add_grain_texture(self, draw, shape_coords, color, type="wood"):
        # Procedural texture logic: adds dots and lines to make surfaces look real
        r, g, b = color
        for _ in range(300):
            tx = random.randint(shape_coords[0], shape_coords[2])
            ty = random.randint(shape_coords[1], shape_coords[3])
            variation = random.randint(-20, 20)
            draw.point((tx, ty), fill=(max(0,r+variation), max(0,g+variation), max(0,b+variation)))

    def generate(self, prompt, model):
        res = 1024 if "Pro" in model else 512
        img = Image.new('RGB', (res, res), (30, 35, 45))
        draw = ImageDraw.Draw(img)
        
        # Ground and Sky with basic gradients
        draw.rectangle([0, 0, res, res//2], fill=(135, 206, 250)) # Sky
        draw.rectangle([0, res//2, res, res], fill=(34, 139, 34)) # Grass
        
        # Apply texture to the grass
        for _ in range(1000):
            gx, gy = random.randint(0, res), random.randint(res//2, res)
            draw.line([(gx, gy), (gx, gy-5)], fill=(20, 100, 20), width=1)

        # Smart Object detection (Example: House)
        if "house" in prompt.lower():
            coords = [res//4, res//2-100, res//4+200, res//2+50]
            draw.rectangle(coords, fill=(139, 69, 19))
            self.add_grain_texture(draw, coords, (139, 69, 19)) # Add Wood Grain
            draw.polygon([(res//4-20, res//2-100), (res//4+100, res//2-180), (res//4+220, res//2-100)], fill=(150, 0, 0)) # Roof

        # Branding
        draw.text((10, res-30), "Ludy 1.2 Texture-Engine", fill="white")
        return img

# --- THE APP INTERFACE ---
if "brain" not in st.session_state: st.session_state.brain = SmartBotBrain()
if "messages" not in st.session_state: st.session_state.messages = []

st.title("🤖 SmartBot AI")
st.caption("Powered by the Ludy Image Engine")

# Display Chat History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if "image" in m: st.image(m["image"])

# Input
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        # IMAGE GENERATION
        if any(x in prompt.lower() for x in ["draw", "generate", "image", "picture"]):
            ludy = LudyGenerator()
            img = ludy.generate(prompt, "Pro")
            st.image(img, caption="Ludy is done rendering.")
            st.session_state.messages.append({"role": "assistant", "content": "I painted this for you:", "image": img})
        
        # CONVERSATION & SEARCH
        else:
            response = st.session_state.brain.get_response(prompt)
            st.write(response)
            
            # AUDIO OUTPUT
            clean_text = re.sub(r'[*#_]', '', response) # Clean markdown for voice
            tts = gTTS(text=clean_text, lang='en')
            tts.save("speech.mp3")
            st.audio("speech.mp3", autoplay=True)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
