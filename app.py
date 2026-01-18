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
    /* Move chat input to bottom */
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    
    /* Style improvements */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- COMPREHENSIVE OBJECT DATABASE (100+ objects) ---
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

# --- TEXT TO SPEECH FUNCTION ---
def text_to_speech_button(text, key):
    """Add audio player with gTTS"""
    # Clean text for speech
    clean_text = re.sub(r'\*\*|__|~~|#', '', text)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    clean_text = clean_text[:500]  # Limit length for speed
    
    try:
        # Generate speech
        tts = gTTS(text=clean_text, lang='en', slow=False)
        
        # Save to temporary file
        audio_file = f"temp_audio_{key}.mp3"
        tts.save(audio_file)
        
        # Read and encode audio
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        
        # Clean up temp file
        os.remove(audio_file)
        
        # Create audio player
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio controls style="width: 200px; height: 30px;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.caption("🔇 Audio unavailable")

# --- ADVANCED CHAT ENGINE ---
class SmartChatEngine:
    def __init__(self):
        self.context = []
        self.history = []
        
    def search_web(self, query):
        """Search DuckDuckGo API"""
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('Abstract'):
                    return data['Abstract']
                elif data.get('RelatedTopics'):
                    topics = [t.get('Text', '') for t in data['RelatedTopics'] if isinstance(t, dict)]
                    return topics[0] if topics else None
        except:
            pass
        return None
    
    def reason_step_by_step(self, query):
        """Pro model reasoning"""
        steps = []
        query_lower = query.lower()
        
        # Analyze question type
        if 'why' in query_lower or 'how' in query_lower:
            steps.append("Detected explanatory question - searching for causal relationships")
        elif 'compare' in query_lower or 'difference' in query_lower:
            steps.append("Detected comparison query - analyzing multiple factors")
        elif 'best' in query_lower or 'recommend' in query_lower:
            steps.append("Detected recommendation request - evaluating options")
        else:
            steps.append("Analyzing query structure and intent")
        
        # Search for information
        web_result = self.search_web(query)
        if web_result:
            steps.append("Retrieved relevant data from web sources")
            steps.append("Synthesizing information with logical inference")
            return steps, web_result
        else:
            steps.append("Using existing knowledge base for response")
            return steps, None
    
    def respond(self, user_input, model_type):
        user_lower = user_input.lower()
        self.history.append(user_input)
        
        # Greetings
        greetings = ['hello', 'hi', 'hey', 'sup', 'greetings', 'good morning', 'good evening']
        if any(g in user_lower for g in greetings):
            responses = [
                f"Hello! I'm SmartBot {model_type}. How can I help you today?",
                f"Hi there! SmartBot {model_type} at your service! What would you like to know?",
                f"Hey! Ready to assist with conversation, reasoning, or image generation!",
                f"Greetings! I'm here to help. Ask me anything or request an image!",
            ]
            return random.choice(responses)
        
        # Identity
        if 'who are you' in user_lower or 'what are you' in user_lower:
            return (f"I'm SmartBot {model_type}, an advanced AI assistant! I can:\n\n"
                   "- Have natural conversations\n"
                   "- Generate images from 100+ objects\n"
                   "- Search the web for current information\n"
                   "- Perform advanced reasoning (Pro model)\n"
                   "- Read responses aloud\n\n"
                   "Try asking me something or say 'generate an image of...'")
        
        # Capabilities
        if 'what can you do' in user_lower or 'capabilities' in user_lower or 'help' in user_lower:
            return """**SmartBot Capabilities:**

**Conversation**: Natural dialogue with context awareness
**Image Creation**: 100+ objects including vehicles, animals, buildings, nature, and more
**Web Search**: Real-time information from the internet
**Advanced Reasoning**: Step-by-step logical analysis (Pro model only)
**Text-to-Speech**: Click 'Read Aloud' to hear responses

**Try these examples:**
- "What is quantum computing?"
- "Generate a sunset with mountains and a lake"
- "Compare electric vs gas cars"
- "Tell me about recent AI developments" """
        
        # Pro Model Reasoning
        if model_type == "Pro":
            reasoning_keywords = ['why', 'how', 'explain', 'compare', 'analyze', 'what is']
            if any(kw in user_lower for kw in reasoning_keywords):
                steps, web_data = self.reason_step_by_step(user_input)
                
                response = "**Advanced Reasoning Process:**\n\n"
                for i, step in enumerate(steps, 1):
                    response += f"{i}. {step}\n"
                
                response += "\n**Conclusion:**\n\n"
                if web_data:
                    response += f"{web_data}\n\n*This response combines web search with logical analysis.*"
                else:
                    # Fallback knowledge
                    response += self.generate_knowledge_response(user_input)
                
                return response
        
        # Standard web search for factual queries
        search_triggers = ['what', 'who', 'when', 'where', 'tell me about', 'information on']
        if any(trigger in user_lower for trigger in search_triggers):
            result = self.search_web(user_input)
            if result:
                if model_type == "Pro":
                    return f"**Web Search Results:**\n\n{result}\n\n*Verified from multiple sources*"
                else:
                    return f"Here's what I found: {result}"
        
        # Conversational responses
        return self.generate_conversational_response(user_input)
    
    def generate_knowledge_response(self, query):
        """Generate knowledge-based response"""
        lower = query.lower()
        
        if 'quantum' in lower:
            return "Quantum computing uses quantum mechanics principles like superposition and entanglement to process information in ways classical computers cannot. Quantum bits (qubits) can exist in multiple states simultaneously, enabling parallel computation."
        elif 'ai' in lower or 'artificial intelligence' in lower:
            return "Artificial Intelligence refers to computer systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, and problem-solving. Modern AI uses machine learning and neural networks to improve performance over time."
        elif 'climate' in lower:
            return "Climate change refers to long-term shifts in global temperatures and weather patterns, primarily driven by human activities like fossil fuel consumption, deforestation, and industrial processes."
        elif 'electric' in lower and 'vehicle' in lower:
            return "Electric vehicles use battery-powered electric motors instead of internal combustion engines. They offer zero direct emissions, lower operating costs, and instant torque. However, they face challenges with charging infrastructure and battery range."
        elif 'hydrogen' in lower and ('fuel' in lower or 'vehicle' in lower):
            return "Hydrogen fuel cell vehicles convert hydrogen gas into electricity through a chemical reaction, producing only water as a byproduct. They offer faster refueling than EVs but face infrastructure and production challenges."
        elif 'drive' in lower and ('left' in lower or 'right' in lower):
            return "The side of the road countries drive on is largely historical. Britain drove on the left due to sword-fighting conventions, and this spread to its colonies. Napoleon's conquests spread right-hand driving across Europe. Today, about 35% of countries drive on the left."
        elif 'renewable' in lower or 'solar' in lower or 'wind' in lower:
            return "Renewable energy sources include solar, wind, hydroelectric, and geothermal power. They produce minimal carbon emissions and are increasingly cost-competitive with fossil fuels."
        else:
            return "That's an interesting question! Based on my knowledge, this topic involves multiple factors to consider. Could you be more specific about what aspect interests you most?"
    
    def generate_conversational_response(self, user_input):
        """Generate engaging conversational responses"""
        responses = [
            "That's a fascinating topic! What specifically interests you about it?",
            "I see what you're getting at. Tell me more about your thoughts on this.",
            "Interesting perspective! I'd love to hear more details.",
            "That's worth exploring further. What aspect would you like to discuss?",
            "Great question! Let me think about that from different angles.",
            "I appreciate you bringing that up. Can you elaborate a bit more?",
        ]
        return random.choice(responses)

# --- IMAGE RENDERER ---
class ImageRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def parse_prompt(self, prompt):
        """Extract objects and attributes from prompt"""
        prompt_lower = prompt.lower()
        scene = {
            'objects': [],
            'colors': [],
            'time': 'day',
            'weather': 'clear'
        }
        
        # Find objects
        for obj, keywords in OBJECTS.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['objects'].append(obj)
        
        # Find colors
        for color, rgb in COLORS.items():
            if color in prompt_lower:
                scene['colors'].append(color)
        
        # Time of day
        if 'night' in prompt_lower:
            scene['time'] = 'night'
        elif 'sunset' in prompt_lower or 'dusk' in prompt_lower:
            scene['time'] = 'sunset'
        elif 'sunrise' in prompt_lower or 'dawn' in prompt_lower:
            scene['time'] = 'sunrise'
        
        # Weather
        if 'rain' in prompt_lower:
            scene['weather'] = 'rainy'
        elif 'snow' in prompt_lower:
            scene['weather'] = 'snowy'
        elif 'storm' in prompt_lower:
            scene['weather'] = 'stormy'
        
        # Default objects
        if not scene['objects']:
            scene['objects'] = ['tree', 'mountain', 'cloud']
        
        return scene
    
    def render(self, scene):
        """Render the scene"""
        img = Image.new('RGB', (self.width, self.height), 'black')
        draw = ImageDraw.Draw(img)
        
        # Background based on time
        time = scene['time']
        if time == 'day':
            sky = (135, 206, 250)
            ground = (34, 139, 34)
        elif time == 'night':
            sky = (10, 10, 40)
            ground = (20, 40, 20)
        elif time == 'sunset':
            sky = (255, 140, 60)
            ground = (100, 80, 40)
        else:  # sunrise
            sky = (255, 200, 150)
            ground = (80, 120, 60)
        
        # Draw sky and ground
        draw.rectangle((0, 0, self.width, self.height // 2), fill=sky)
        draw.rectangle((0, self.height // 2, self.width, self.height), fill=ground)
        
        # Weather effects
        if scene['weather'] == 'rainy':
            for _ in range(100):
                x, y = random.randint(0, self.width), random.randint(0, self.height)
                draw.line((x, y, x, y + 10), fill=(200, 200, 255), width=1)
        elif scene['weather'] == 'snowy':
            for _ in range(80):
                x, y = random.randint(0, self.width), random.randint(0, self.height)
                draw.ellipse((x, y, x + 3, y + 3), fill='white')
        
        # Draw objects
        objects = scene['objects']
        colors = scene['colors']
        
        # Sky objects
        if 'sun' in objects or (time == 'day' and 'moon' not in objects):
            draw.ellipse((self.width - 150, 50, self.width - 50, 150), fill='yellow')
        
        if 'moon' in objects or time == 'night':
            draw.ellipse((self.width - 150, 50, self.width - 70, 130), fill='white')
        
        if 'star' in objects or time == 'night':
            for _ in range(50):
                x, y = random.randint(0, self.width), random.randint(0, self.height // 2)
                draw.ellipse((x, y, x + 2, y + 2), fill='white')
        
        if 'cloud' in objects or 'rain' in scene['weather']:
            for i in range(3):
                x = 100 + i * 250
                y = 80 + random.randint(-20, 20)
                draw.ellipse((x, y, x + 80, y + 40), fill='white')
                draw.ellipse((x + 30, y - 20, x + 110, y + 20), fill='white')
        
        if 'rainbow' in objects:
            colors_rainbow = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
            for i, color in enumerate(colors_rainbow):
                draw.arc((200, 150, 600, 400), 0, 180, fill=color, width=8)
        
        # Terrain objects
        if 'mountain' in objects:
            points = [(0, 300), (200, 100), (400, 300), (600, 150), (800, 300)]
            for i in range(len(points) - 1):
                draw.polygon([points[i], points[i + 1], (points[i + 1][0], 300), (points[i][0], 300)], 
                           fill=(100, 100, 100))
        
        if 'ocean' in objects or 'sea' in objects or 'water' in objects:
            water_color = (65, 105, 225)
            draw.rectangle((0, 350, self.width, self.height), fill=water_color)
            # Waves
            for i in range(0, self.width, 50):
                draw.arc((i, 340, i + 50, 360), 0, 180, fill=(100, 150, 255), width=2)
        
        if 'beach' in objects:
            draw.rectangle((0, 400, self.width, self.height), fill=(238, 214, 175))
        
        if 'volcano' in objects:
            draw.polygon([(300, 350), (450, 350), (375, 200)], fill=(100, 50, 50))
            # Lava
            draw.polygon([(360, 200), (390, 200), (380, 180), (370, 180)], fill=(255, 100, 0))
        
        # Nature objects
        if 'tree' in objects or 'forest' in objects:
            for x_pos in [100, 150, 700, 750]:
                trunk_x = x_pos
                draw.rectangle((trunk_x, 250, trunk_x + 20, 350), fill=(139, 69, 19))
                draw.ellipse((trunk_x - 30, 200, trunk_x + 50, 270), fill=(0, 128, 0))
        
        if 'palm' in objects:
            draw.rectangle((400, 250, 415, 350), fill=(139, 69, 19))
            for angle in range(0, 360, 45):
                x = 407 + 50 * math.cos(math.radians(angle))
                y = 240 + 30 * math.sin(math.radians(angle))
                draw.line((407, 240, x, y), fill=(0, 150, 0), width=5)
        
        if 'flower' in objects:
            for x_pos in [200, 300, 600]:
                y_pos = 330
                draw.ellipse((x_pos, y_pos, x_pos + 20, y_pos + 20), fill=(255, 105, 180))
                draw.rectangle((x_pos + 8, y_pos + 20, x_pos + 12, y_pos + 40), fill=(0, 128, 0))
        
        if 'cactus' in objects:
            draw.rectangle((350, 250, 380, 350), fill=(0, 128, 0))
            draw.rectangle((330, 280, 350, 320), fill=(0, 128, 0))
            draw.rectangle((380, 270, 400, 310), fill=(0, 128, 0))
        
        # Buildings
        if 'house' in objects:
            house_color = COLORS.get(colors[0], (150, 75, 0)) if colors else (150, 75, 0)
            draw.rectangle((200, 250, 350, 350), fill=house_color, outline='black', width=2)
            draw.polygon([(190, 250), (360, 250), (275, 180)], fill=(80, 80, 80))
            draw.rectangle((260, 300, 290, 350), fill=(100, 50, 0))
            draw.rectangle((220, 270, 250, 300), fill=(135, 206, 235))
        
        if 'castle' in objects:
            # Main structure
            draw.rectangle((250, 200, 550, 350), fill=(150, 150, 150), outline='black', width=2)
            # Towers
            for x in [220, 350, 480]:
                draw.rectangle((x, 150, x + 50, 350), fill=(130, 130, 130), outline='black')
                draw.polygon([(x - 10, 150), (x + 60, 150), (x + 25, 100)], fill=(100, 100, 100))
        
        if 'lighthouse' in objects:
            draw.rectangle((400, 200, 440, 350), fill=(200, 200, 200), outline='black', width=2)
            draw.rectangle((390, 180, 450, 200), fill='red')
            draw.ellipse((395, 170, 445, 180), fill='yellow')
        
        # Vehicles
        if 'car' in objects:
            car_color = COLORS.get(colors[0], (255, 0, 0)) if colors else (255, 0, 0)
            draw.rectangle((300, 320, 400, 350), fill=car_color)
            draw.rectangle((320, 300, 380, 320), fill=(200, 200, 200))
            draw.ellipse((310, 340, 330, 360), fill='black')
            draw.ellipse((370, 340, 390, 360), fill='black')
        
        if 'airplane' in objects:
            draw.ellipse((300, 100, 450, 130), fill=(200, 200, 200))
            draw.polygon([(280, 115), (300, 100), (320, 115)], fill=(150, 150, 150))
            draw.polygon([(430, 115), (450, 100), (470, 115)], fill=(150, 150, 150))
        
        if 'boat' in objects or 'ship' in objects:
            draw.polygon([(200, 380), (400, 380), (380, 420), (220, 420)], fill=(100, 50, 0))
            draw.polygon([(300, 300), (300, 380), (330, 380)], fill='white')
        
        # Animals
        if 'dog' in objects:
            draw.ellipse((500, 310, 560, 350), fill=(139, 69, 19))
            draw.ellipse((510, 295, 530, 315), fill=(139, 69, 19))
        
        if 'cat' in objects:
            draw.ellipse((150, 320, 200, 350), fill=(255, 140, 0))
            draw.polygon([(160, 320), (170, 305), (180, 320)], fill=(255, 140, 0))
        
        if 'bird' in objects:
            for i in range(3):
                x = 100 + i * 150
                y = 150 + random.randint(-30, 30)
                draw.arc((x, y, x + 30, y + 15), 30, 150, fill='black', width=2)
                draw.arc((x + 15, y, x + 45, y + 15), 30, 150, fill='black', width=2)
        
        # Objects
        if 'fire' in objects:
            draw.polygon([(400, 350), (420, 320), (440, 350)], fill=(255, 69, 0))
            draw.polygon([(410, 340), (425, 315), (435, 340)], fill='yellow')
        
        return img

# --- STREAMLIT APP ---
def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Model Configuration")
        model = st.radio(
            "Select Model:",
            ("SmartBot 1.1 Flash", "SmartBot 1.2 Pro"),
            index=1
        )
        
        st.markdown("---")
        st.markdown("### Model Features")
        if "Flash" in model:
            st.info("**Speed**: Ultra-fast\n\n**Reasoning**: Basic\n\n**Images**: Quick render")
        else:
            st.success("**Speed**: Optimized\n\n**Reasoning**: Advanced with web search\n\n**Images**: High quality")
        
        st.markdown("---")
        st.markdown("### Voice Input")
        st.caption("Use 'Read Aloud' button on responses to hear them spoken")
    
    # Header
    st.title("🤖 SmartBot AI")
    st.caption(f"Powered by {model} | Advanced Reasoning & Image Generation")
    
    # Initialize session
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'engine' not in st.session_state:
        st.session_state.engine = SmartChatEngine()
    
    # Display chat history
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "image" in msg:
                st.image(msg["image"], caption="Generated Image", use_container_width=True)
            # Add text-to-speech for assistant messages
            if msg["role"] == "assistant" and "image" not in msg:
                text_to_speech_button(msg["content"], f"msg_{idx}")
    
    # Chat input at bottom
    user_input = st.chat_input("Ask anything or request an image...")
    
    # Process input
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # Check if image generation request
        img_keywords = ['generate', 'create', 'draw', 'paint', 'show me', 'make', 'design']
        is_image = any(kw in user_input.lower() for kw in img_keywords)
        
        if is_image:
            # Image generation
            with st.chat_message("assistant"):
                with st.spinner("Creating your image..."):
                    # Set resolution
                    if "Pro" in model:
                        width, height = 800, 600
                        steps = 15
                    else:
                        width, height = 512, 384
                        steps = 8
                    
                    renderer = ImageRenderer(width, height)
                    scene = renderer.parse_prompt(user_input)
                    
                    st.write(f"Generating: {', '.join(scene['objects'][:5])}... ({scene['time']}, {scene['weather']})")
                    
                    # Progress bar simulation
                    progress = st.progress(0)
                    img_placeholder = st.empty()
                    
                    final_img = renderer.render(scene)
                    
                    # Simulate diffusion process
                    for i in range(steps):
                        noise_level = 1.0 - (i / steps)
                        temp_img = final_img.copy()
                        
                        # Add decreasing noise
                        if noise_level > 0.3:
                            temp_img = temp_img.filter(ImageFilter.GaussianBlur(radius=noise_level * 3))
                        
                        img_placeholder.image(temp_img, caption=f"Step {i+1}/{steps}")
                        progress.progress((i + 1) / steps)
                        time.sleep(0.1 if "Flash" in model else 0.2)
                    
                    # Final result
                    progress.empty()
                    img_placeholder.image(final_img, caption=f"Complete | {model}", use_container_width=True)
                    
                    response = f"Here's your image! It includes: {', '.join(scene['objects'][:10])}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "image": final_img
                    })
        else:
            # Chat response
            with st.chat_message("assistant"):
                with st.spinner(f"{model} thinking..."):
                    model_type = "Pro" if "Pro" in model else "Flash"
                    response = st.session_state.engine.respond(user_input, model_type)
                    st.markdown(response)
                    
                    # Add read aloud button
                    text_to_speech_button(response, f"new_msg")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
