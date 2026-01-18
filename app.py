import streamlit as st
from huggingface_hub import InferenceClient

# Branding
st.set_page_config(page_title="SmartBot AI Pro", page_icon="🤖")
st.title("🤖 SmartBot AI Pro")

# Load Secret
HF_TOKEN = st.secrets.get("HUGGINGFACE_API_TOKEN")

# Branded Models (Updated for 2026)
MODELS = {
    "SmartBot 1.2 Flash": "HuggingFaceH4/zephyr-7b-beta",
    "SmartBot 2.1 Pro": "mistralai/Mistral-7B-Instruct-v0.3"
}

if not HF_TOKEN:
    st.error("🔑 API Key Missing! Go to Streamlit Settings > Secrets and add HUGGINGFACE_API_TOKEN")
    st.stop()

# Initialize 2026-Ready Client
client = InferenceClient(api_key=HF_TOKEN)

selected_model = st.sidebar.selectbox("SmartBot Version", list(MODELS.keys()))

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask SmartBot..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # The key fix: Using chat_completion with streaming
        response_stream = client.chat_completion(
            model=MODELS[selected_model],
            messages=[
                {"role": "system", "content": f"You are {selected_model}."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            stream=True
        )
        
        full_response = st.write_stream(response_stream)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
