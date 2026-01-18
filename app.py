import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io

# --- SMARTBOT BRANDING CONFIG ---
st.set_page_config(page_title="SmartBot AI Pro", page_icon="🤖")

# Custom CSS for Branded Look
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stChatFloatingInputContainer { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

# Access Token from Streamlit Secrets
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_TOKEN")

# Branded Model Map (Internal mapping to real engines)
SMARTBOT_VERSIONS = {
    "SmartBot 1.2 Flash": "HuggingFaceH4/zephyr-7b-beta",
    "SmartBot 2.1 Pro": "mistralai/Mistral-7B-Instruct-v0.3"
}

# --- CORE ENGINE ---
class SmartBot:
    def __init__(self, token):
        # The new client automatically uses router.huggingface.co
        self.client = InferenceClient(api_key=token)

    def chat(self, prompt, version):
        model_id = SMARTBOT_VERSIONS[version]
        
        # Branding Guard: Forces AI to stay in character
        system_prompt = f"You are {version}, a state-of-the-art AI. Never mention Hugging Face or other companies."
        
        try:
            # Using the new provider-based chat completion
            response = ""
            for message in self.client.chat_completion(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                stream=True,
                provider="hf-inference" # Forces the free serverless tier
            ):
                token_text = message.choices[0].delta.content
                if token_text:
                    response += token_text
            return response
        except Exception as e:
            return f"⚠️ SmartBot Connection Error: {str(e)}"

    def draw(self, prompt):
        try:
            # Standardizing on a reliable image model for mobile hotspots
            image = self.client.text_to_image(prompt, model="stabilityai/stable-diffusion-2-1")
            return image
        except:
            return None

# --- UI INTERFACE ---
def main():
    st.title("🤖 SmartBot AI Pro")
    st.caption("Model Version: 2026.1 (Stable)")

    if not HF_TOKEN:
        st.error("🔑 API Key not found in Secrets! Please check .streamlit/secrets.toml")
        return

    bot = SmartBot(HF_TOKEN)

    with st.sidebar:
        st.header("SmartBot Settings")
        selected_version = st.radio("Select SmartBot Version:", list(SMARTBOT_VERSIONS.keys()))
        st.divider()
        st.write("📡 Connection: Mobile Hotspot Optimized")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask SmartBot anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if any(word in prompt.lower() for word in ["draw", "image", "generate"]):
                with st.spinner("🎨 SmartBot is creating..."):
                    img = bot.draw(prompt)
                    if img:
                        st.image(img)
                        st.session_state.messages.append({"role": "assistant", "content": "Image generated."})
                    else:
                        st.error("Drawing failed. Check your hotspot connection.")
            else:
                with st.spinner(f"🧠 {selected_version} is thinking..."):
                    response = bot.chat(prompt, selected_version)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
