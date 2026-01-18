# =====================================
#          CONFIGURATION PART
# =====================================

import os
import streamlit as st
from openai import OpenAI

# ── Choose your provider ────────────────────────────────
# Uncomment only one block!

# === Groq ===
BASE_URL = "https://api.groq.com/openai/v1"
API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

# === Together AI === (alternative)
# BASE_URL = "https://api.together.xyz/v1"
# API_KEY = st.secrets.get("TOGETHER_API_KEY") or os.getenv("TOGETHER_API_KEY")

# === OpenRouter === (another good alternative)
# BASE_URL = "https://openrouter.ai/api/v1"
# API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("API key not found! Please set it in .streamlit/secrets.toml or environment variables.")
    st.stop()

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# Model mapping - this is the only place where real model names live
MODEL_MAPPING = {
    "SmartBot 1.1 Flash": "llama-3.1-8b-instant",           # Groq example
    # "SmartBot 1.1 Flash": "meta-llama/Llama-3.2-3B-Instruct",     # Together example
    # "SmartBot 1.1 Flash": "nousresearch/hermes-3-llama-3.1-405b:free",  # OpenRouter free example

    "SmartBot 1.2 Pro":   "mixtral-8x7b-32768",             # Groq example
    # "SmartBot 1.2 Pro":   "meta-llama/Llama-3.1-70B-Instruct",        # Together
    # "SmartBot 1.2 Pro":   "anthropic/claude-3.5-sonnet",             # OpenRouter (paid)
}

# System prompt that protects your branding
SYSTEM_PROMPT = """You are SmartBot - helpful, friendly and truthful AI assistant.
You MUST always identify yourself ONLY as SmartBot.
Never mention any real model name, provider, company, API or backend technology you are using.
Never say you are based on Llama, Mixtral, Claude, GPT, Groq, Together, OpenRouter etc.
If asked about your model/technology - say variations of:
- "I'm SmartBot, a custom AI created for helpful conversations and creative tasks"
- "I'm just SmartBot 😊 - nice to meet you!"
- "My creators call me SmartBot - that's all you need to know!"
Keep answers natural and fun."""

# =====================================
#          CHAT ENGINE
# =====================================

class SmartChatEngine:
    def __init__(self):
        self.context = [{"role": "system", "content": SYSTEM_PROMPT}]

    def respond(self, user_input, selected_ui_model):
        real_model = MODEL_MAPPING.get(selected_ui_model)

        if not real_model:
            return "Sorry, selected model configuration is invalid."

        messages = self.context + [{"role": "user", "content": user_input}]

        try:
            with st.spinner("SmartBot is thinking..."):
                completion = client.chat.completions.create(
                    model=real_model,
                    messages=messages,
                    temperature=0.75,
                    max_tokens=2048,
                    stream=False
                )

            response = completion.choices[0].message.content.strip()

            # Keep history (limited)
            self.context.append({"role": "user", "content": user_input})
            self.context.append({"role": "assistant", "content": response})
            if len(self.context) > 15:
                self.context = [self.context[0]] + self.context[-14:]  # keep system + last 7 turns

            return response

        except Exception as e:
            return f"😓 SmartBot encountered an issue...\n\n({str(e)})"

# =====================================
#          SIDEBAR - clean branding
# =====================================

with st.sidebar:
    st.header("SmartBot Settings")
    
    model_choice = st.radio(
        "Model Version",
        ["SmartBot 1.1 Flash", "SmartBot 1.2 Pro"],
        index=1,
        help="Flash = faster • Pro = smarter & more detailed"
    )
    
    st.markdown("---")
    with st.expander("ℹ️ About SmartBot", expanded=False):
        st.markdown("""
        SmartBot is a custom conversational AI with image generation capabilities.
        
        • Fast answers  
        • Creative image generation  
        • Remembers conversation context  
        • Voice output support
        """)

# ... rest of your app remains almost the same ...

# Just change how you call the engine:
response = st.session_state.engine.respond(user_input, model_choice)
