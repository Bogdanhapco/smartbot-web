import streamlit as st
from huggingface_hub import InferenceClient

# --- SMARTBOT BRANDING ---
st.set_page_config(page_title="SmartBot AI Pro", page_icon="🤖", layout="centered")

# Branded internal mapping
SMARTBOT_MODELS = {
    "SmartBot 1.2 Flash": "HuggingFaceH4/zephyr-7b-beta",
    "SmartBot 2.1 Pro": "mistralai/Mistral-7B-Instruct-v0.3"
}

# Securely grab the key from the Cloud Secrets dashboard
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_TOKEN")

st.title("🤖 SmartBot AI Pro")
st.caption("Powered by SmartBot Core v2026.1")

if not HF_TOKEN:
    st.error("🔑 API Token Missing! Add it to the Streamlit Cloud Secrets dashboard.")
    st.stop()

# Initialize Client
client = InferenceClient(api_key=HF_TOKEN)

with st.sidebar:
    st.header("SmartBot Settings")
    version = st.radio("Select Model:", list(SMARTBOT_MODELS.keys()))
    st.info("Public Web Version - Optimized for Mobile")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("How can SmartBot help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_area = st.empty()
        full_text = ""
        
        # Identity injection to keep branding strict
        system_prompt = f"You are {version}. You are a helpful AI assistant."
        
        # STREAMING: Essential for stable performance on hotspots
        try:
            for chunk in client.chat_completion(
                model=SMARTBOT_MODELS[version],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=1000,
                stream=True,
            ):
                content = chunk.choices[0].delta.content
                if content:
                    full_text += content
                    response_area.markdown(full_text + "▌")
            
            response_area.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})
        except Exception as e:
            st.error(f"📡 Connection dropped. Try again! (Error: {e})")
