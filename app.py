import os
import re
import json
import math
import random
import time
import requests
from PIL import Image, ImageDraw, ImageFilter
import streamlit as st
from gtts import gTTS
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="SmartBot AI Pro", layout="centered")

# Add custom CSS
st.markdown("""
<style>
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stButton>button {
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Get API token from secrets
try:
    HF_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]
except:
    HF_TOKEN = None
    st.error("⚠️ Please add your Hugging Face API token to Streamlit secrets!")

# --- AI MODEL CONFIGURATION ---
MODELS = {
    "Flash": {
        "name": "SmartBot 1.2 Flash",
        "display_name": "SmartBot 1.2 Flash",
        "api_url": "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct",
        "max_tokens": 512,
        "temperature": 0.7,
    },
    "Pro": {
        "name": "SmartBot 2.1 Pro 7B",
        "display_name": "SmartBot 2.1 Pro 7B", 
        "api_url": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
        "max_tokens": 1024,
        "temperature": 0.8,
    }
}

# Image generation model
IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

# --- COMPREHENSIVE OBJECT DATABASE ---
OBJECTS = {
    'car': ['car', 'vehicle'], 'truck': ['truck'], 'bus': ['bus'], 'train': ['train'],
    'airplane': ['airplane', 'plane'], 'helicopter': ['helicopter'], 'boat': ['boat', 'ship'],
    'bicycle': ['bicycle', 'bike'], 'motorcycle': ['motorcycle'], 'rocket': ['rocket'],
    'house': ['house', 'home'], 'building': ['building', 'skyscraper'], 'castle': ['castle'],
    'church': ['church'], 'tower': ['tower'], 'bridge': ['bridge'], 'barn': ['barn'],
    'lighthouse': ['lighthouse'], 'tent': ['tent'], 'pyramid': ['pyramid'],
    'tree': ['tree'], 'pine': ['pine'], 'palm': ['palm'], 'flower': ['flower'],
    'rose': ['rose'], 'sunflower': ['sunflower'], 'grass': ['grass'], 'bush': ['bush'],
    'cactus': ['cactus'], 'mushroom': ['mushroom'], 'bamboo': ['bamboo'],
    'mountain': ['mountain'], 'hill': ['hill'], 'valley': ['valley'], 'volcano': ['volcano'],
    'desert': ['desert'], 'beach': ['beach'], 'island': ['island'], 'cliff': ['cliff'],
    'cave': ['cave'], 'rock': ['rock', 'boulder'],
    'ocean': ['ocean', 'sea'], 'lake': ['lake'], 'river': ['river'], 'pond': ['pond'],
    'waterfall': ['waterfall'], 'waves': ['waves'], 'reef': ['reef'],
    'sun': ['sun'], 'moon': ['moon'], 'star': ['star'], 'cloud': ['cloud'],
    'rainbow': ['rainbow'], 'lightning': ['lightning'], 'tornado': ['tornado'],
    'rain': ['rain'], 'snow': ['snow'], 'aurora': ['aurora', 'northern lights'],
    'dog': ['dog', 'puppy'], 'cat': ['cat', 'kitten'], 'horse': ['horse'],
    'cow': ['cow'], 'sheep': ['sheep'], 'pig': ['pig'], 'rabbit': ['rabbit'],
    'deer': ['deer'], 'bear': ['bear'], 'wolf': ['wolf'], 'fox': ['fox'],
    'lion': ['lion'], 'tiger': ['tiger'], 'elephant': ['elephant'], 'giraffe': ['giraffe'],
    'zebra': ['zebra'], 'monkey': ['monkey'], 'panda': ['panda'], 'kangaroo': ['kangaroo'],
    'bird': ['bird'], 'eagle': ['eagle'], 'owl': ['owl'], 'parrot': ['parrot'],
    'penguin': ['penguin'], 'flamingo': ['flamingo'], 'swan': ['swan'], 'duck': ['duck'],
    'chicken': ['chicken'], 'peacock': ['peacock'],
    'snake': ['snake'], 'turtle': ['turtle'], 'frog': ['frog'], 'crocodile': ['crocodile'],
    'dragon': ['dragon'], 'dinosaur': ['dinosaur'],
    'butterfly': ['butterfly'], 'bee': ['bee'], 'ant': ['ant'], 'spider': ['spider'],
    'dragonfly': ['dragonfly'], 'ladybug': ['ladybug'],
    'fish': ['fish'], 'shark': ['shark'], 'dolphin': ['dolphin'], 'whale': ['whale'],
    'jellyfish': ['jellyfish'], 'octopus': ['octopus'], 'crab': ['crab'], 'starfish': ['starfish'],
    'person': ['person', 'human'], 'man': ['man'], 'woman': ['woman'], 'child': ['child'],
    'family': ['family'], 'crowd': ['crowd'], 'superhero': ['superhero'],
    'robot': ['robot', 'android'], 'alien': ['alien'],
    'chair': ['chair'], 'table': ['table'], 'bed': ['bed'], 'sofa': ['sofa'],
    'lamp': ['lamp'], 'clock': ['clock'], 'mirror': ['mirror'], 'window': ['window'],
    'door': ['door'], 'stairs': ['stairs'], 'fence': ['fence'],
    'phone': ['phone'], 'computer': ['computer'], 'tv': ['tv', 'television'],
    'camera': ['camera'], 'book': ['book'], 'umbrella': ['umbrella'], 'backpack': ['backpack'],
    'ball': ['ball'], 'balloon': ['balloon'], 'kite': ['kite'], 'flag': ['flag'],
    'apple': ['apple'], 'banana': ['banana'], 'orange': ['orange'], 'pizza': ['pizza'],
    'cake': ['cake'], 'ice cream': ['ice cream'], 'bread': ['bread'], 'burger': ['burger'],
    'guitar': ['guitar'], 'piano': ['piano'], 'drum': ['drum'], 'violin': ['violin'],
    'fire': ['fire', 'flame'], 'smoke': ['smoke'], 'crystal': ['crystal'], 'diamond': ['diamond'],
    'crown': ['crown'], 'sword': ['sword'], 'shield': ['shield'],
    'road': ['road', 'street'], 'path': ['path'], 'garden': ['garden'], 'park': ['park'],
    'city': ['city'], 'village': ['village'], 'farm': ['farm'], 'forest': ['forest'],
}

COLORS = {
    'red': (220, 20, 60), 'blue': (30, 144, 255), 'green': (34, 139, 34),
    'yellow': (255, 215, 0), 'orange': (255, 140, 0), 'purple': (138, 43, 226),
    'pink': (255, 105, 180), 'brown': (139, 69, 19), 'black': (20, 20, 20),
    'white': (245, 245, 245), 'gray': (128, 128, 128), 'gold': (255, 215, 0),
}

# --- TEXT TO SPEECH ---
def text_to_speech_button(text, key):
    """Add audio player with gTTS"""
    clean_text = re.sub(r'\*\*|__|~~|#', '', text)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    clean_text = clean_text[:500]
    
    try:
        tts = gTTS(text=clean_text, lang='en', slow=False)
        audio_file = f"temp_audio_{key}.mp3"
        tts.save(audio_file)
        
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        
        os.remove(audio_file)
        
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio controls style="width: 200px; height: 30px;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.caption("🔇 Audio unavailable")

# --- AI CHAT ENGINE ---
class SmartBotAI:
    def __init__(self, api_token):
        self.api_token = api_token
        self.conversation_history = []
        
    def create_system_prompt(self, model_type):
        """Create system prompt that makes AI identify as SmartBot"""
        model_name = MODELS[model_type]['display_name']
        return f"""You are {model_name}, an advanced AI assistant. 

Key information about you:
- Your name is {model_name}
- You are a helpful, knowledgeable AI assistant
- You can engage in conversations, answer questions, and provide information
- You maintain a friendly and professional tone
- When asked about your identity or what model you are, always say you are {model_name}

Respond naturally and helpfully to the user's questions."""

    def call_ai_model(self, prompt, model_type):
        """Call Hugging Face API with fallback URLs"""
        if not self.api_token:
            return "❌ API token not configured. Please add your Hugging Face token to Streamlit secrets."
        
        model_config = MODELS[model_type]
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Create full prompt with system message
        system_prompt = self.create_system_prompt(model_type)
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": model_config["max_tokens"],
                "temperature": model_config["temperature"],
                "return_full_text": False,
            }
        }
        
        # Try both old and new API endpoints
        api_urls = [
            model_config["api_url"],
            model_config["api_url"].replace("api-inference", "router")  # New endpoint
        ]
        
        last_error = None
        for api_url in api_urls:
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                    return str(result)
                elif response.status_code == 503:
                    return "⏳ Model is loading... Please try again in 20-30 seconds."
                elif response.status_code == 410:
                    # Endpoint deprecated, try next URL
                    continue
                else:
                    last_error = f"Error: {response.status_code}"
                    continue
                    
            except Exception as e:
                last_error = str(e)
                continue
        
        # If all attempts failed
        return f"❌ Unable to connect to AI model. Please try again. ({last_error})"
    
    def respond(self, user_input, model_type):
        """Get AI response"""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Get AI response
        response = self.call_ai_model(user_input, model_type)
        
        # Add to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

# --- IMAGE GENERATOR (AI-POWERED) ---
class AIImageGenerator:
    def __init__(self, api_token):
        self.api_token = api_token
    
    def generate_image(self, prompt):
        """Generate image using Stable Diffusion"""
        if not self.api_token:
            return None, "❌ API token not configured"
        
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Enhance prompt for better results
        enhanced_prompt = f"high quality, detailed, professional: {prompt}"
        
        payload = {
            "inputs": enhanced_prompt,
        }
        
        try:
            response = requests.post(
                IMAGE_MODEL_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                from io import BytesIO
                image = Image.open(BytesIO(response.content))
                return image, None
            elif response.status_code == 503:
                return None, "⏳ Image model is loading... Please try again in 20 seconds."
            else:
                return None, f"❌ Error: {response.status_code}"
                
        except Exception as e:
            return None, f"❌ Error: {str(e)}"

# --- FALLBACK IMAGE RENDERER ---
class FallbackImageRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def parse_prompt(self, prompt):
        """Extract objects from prompt"""
        prompt_lower = prompt.lower()
        scene = {'objects': [], 'colors': [], 'time': 'day', 'weather': 'clear'}
        
        for obj, keywords in OBJECTS.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['objects'].append(obj)
        
        for color, rgb in COLORS.items():
            if color in prompt_lower:
                scene['colors'].append(color)
        
        if 'night' in prompt_lower:
            scene['time'] = 'night'
        elif 'sunset' in prompt_lower:
            scene['time'] = 'sunset'
        
        if 'rain' in prompt_lower:
            scene['weather'] = 'rainy'
        elif 'snow' in prompt_lower:
            scene['weather'] = 'snowy'
        
        if not scene['objects']:
            scene['objects'] = ['tree', 'mountain', 'cloud']
        
        return scene
    
    def render(self, scene):
        """Quick render of scene"""
        img = Image.new('RGB', (self.width, self.height), 'black')
        draw = ImageDraw.Draw(img)
        
        # Background
        time = scene['time']
        if time == 'day':
            sky, ground = (135, 206, 250), (34, 139, 34)
        elif time == 'night':
            sky, ground = (10, 10, 40), (20, 40, 20)
        else:
            sky, ground = (255, 140, 60), (100, 80, 40)
        
        draw.rectangle((0, 0, self.width, self.height // 2), fill=sky)
        draw.rectangle((0, self.height // 2, self.width, self.height), fill=ground)
        
        # Objects
        objects = scene['objects']
        
        if 'sun' in objects or time == 'day':
            draw.ellipse((self.width - 150, 50, self.width - 50, 150), fill='yellow')
        
        if 'moon' in objects or time == 'night':
            draw.ellipse((self.width - 150, 50, self.width - 70, 130), fill='white')
        
        if 'star' in objects or time == 'night':
            for _ in range(50):
                x, y = random.randint(0, self.width), random.randint(0, self.height // 2)
                draw.ellipse((x, y, x + 2, y + 2), fill='white')
        
        if 'cloud' in objects:
            for i in range(3):
                x = 100 + i * 250
                y = 80 + random.randint(-20, 20)
                draw.ellipse((x, y, x + 80, y + 40), fill='white')
        
        if 'mountain' in objects:
            points = [(0, 300), (200, 100), (400, 300), (600, 150), (800, 300)]
            for i in range(len(points) - 1):
                draw.polygon([points[i], points[i + 1], (points[i + 1][0], 300), (points[i][0], 300)], 
                           fill=(100, 100, 100))
        
        if 'tree' in objects:
            for x_pos in [100, 700]:
                draw.rectangle((x_pos, 250, x_pos + 20, 350), fill=(139, 69, 19))
                draw.ellipse((x_pos - 30, 200, x_pos + 50, 270), fill=(0, 128, 0))
        
        if 'house' in objects:
            draw.rectangle((200, 250, 350, 350), fill=(150, 75, 0), outline='black', width=2)
            draw.polygon([(190, 250), (360, 250), (275, 180)], fill=(80, 80, 80))
        
        if 'car' in objects:
            draw.rectangle((300, 320, 400, 350), fill=(255, 0, 0))
            draw.rectangle((320, 300, 380, 320), fill=(200, 200, 200))
            draw.ellipse((310, 340, 330, 360), fill='black')
            draw.ellipse((370, 340, 390, 360), fill='black')
        
        return img

# --- STREAMLIT APP ---
def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Model Configuration")
        model = st.radio(
            "Select Model:",
            ("SmartBot 1.2 Flash", "SmartBot 2.1 Pro 7B"),
            index=1
        )
        
        model_type = "Flash" if "Flash" in model else "Pro"
        
        st.markdown("---")
        st.markdown("### Model Features")
        if model_type == "Flash":
            st.info(f"**Model**: {MODELS['Flash']['display_name']}\n\n**Speed**: Ultra-fast\n\n**Best for**: Quick questions")
        else:
            st.success(f"**Model**: {MODELS['Pro']['display_name']}\n\n**Intelligence**: Advanced\n\n**Best for**: Complex reasoning")
        
        st.markdown("---")
        st.markdown("### Features")
        st.write("✅ Real AI conversations")
        st.write("✅ AI image generation")
        st.write("✅ Text-to-speech")
        st.write("✅ 100% Free")
    
    # Header
    st.title("🤖 SmartBot AI")
    st.caption(f"Powered by {model} | Real AI Models via Hugging Face")
    
    # Initialize session
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = SmartBotAI(HF_TOKEN)
    if 'image_gen' not in st.session_state:
        st.session_state.image_gen = AIImageGenerator(HF_TOKEN)
    
    # Display chat history
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "image" in msg:
                st.image(msg["image"], caption="Generated Image", use_container_width=True)
            if msg["role"] == "assistant" and "image" not in msg:
                text_to_speech_button(msg["content"], f"msg_{idx}")
    
    # Chat input
    user_input = st.chat_input("Ask anything or request an image...")
    
    # Process input
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # Check if image generation request
        img_keywords = ['generate', 'create', 'draw', 'paint', 'show me', 'make', 'design', 'image of']
        is_image = any(kw in user_input.lower() for kw in img_keywords)
        
        if is_image:
            # AI Image generation
            with st.chat_message("assistant"):
                with st.spinner("🎨 Creating your image with AI..."):
                    image, error = st.session_state.image_gen.generate_image(user_input)
                    
                    if image:
                        st.image(image, caption=f"Generated by {model}", use_container_width=True)
                        response = f"Here's your AI-generated image based on: '{user_input}'"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "image": image
                        })
                    else:
                        st.warning(error)
                        st.info("Generating a quick preview instead...")
                        
                        # Fallback to quick render
                        renderer = FallbackImageRenderer(512, 384)
                        scene = renderer.parse_prompt(user_input)
                        fallback_img = renderer.render(scene)
                        
                        st.image(fallback_img, caption="Quick Preview", use_container_width=True)
                        response = f"Created a preview for: '{user_input}'. Try again in 20 seconds for AI generation!"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "image": fallback_img
                        })
        else:
            # AI Chat response
            with st.chat_message("assistant"):
                with st.spinner(f"🤔 {model} thinking..."):
                    response = st.session_state.ai_engine.respond(user_input, model_type)
                    st.markdown(response)
                    text_to_speech_button(response, "new_msg")
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
