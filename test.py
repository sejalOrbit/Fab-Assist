import os
import pandas as pd
import streamlit as st
import requests
import streamlit.components.v1 as components

# Page layout
st.set_page_config(page_title="Fab Engineer Assistant 🤖", layout="centered")
st.markdown("<h1 style='text-align: center;'>🛠️ Fab Engineer Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Ask me your tool or fab-related issues. I’ll guide you with steps to troubleshoot them.</p>", unsafe_allow_html=True)

# Load Excel data
df = pd.read_excel("Queries.xlsx")

# Session history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Autofocus JS
components.html("""
<script>
const input = window.parent.document.querySelector('input[type="text"]');
if (input) {
    input.focus();
}
</script>
""", height=0)

# Helper: flatten context
def get_context(df) -> str:
    return "\n".join(df.astype(str).fillna("").values.flatten())

def get_answer_from_groq(query: str) -> str:
    context = get_context(df)  # Make sure 'df' is defined elsewhere

    headers = {
        "Authorization": f"Bearer {st.secrets['groq_api_key']}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",  # You can change to "qwen-qwq-32b" if needed
        "messages": [
            {
                "role": "system",
                "content": """
You are a concise and helpful assistant for engineers working at semiconductor FABs. For every query, provide clear,
 short, step-by-step guidance using a present-tense, directive tone — like a technician guiding another. Explain 
 possible causes and recommend actions using phrases like "check", "verify", "replace", "ensure", "adjust", etc. 
 Do not copy or repeat exact lines from the context — paraphrase them naturally. Do not repeat the question or provide 
 summaries. Avoid reflective or chatty language, and never say phrases like "Let me", "I see", or long intros. 
 If context is insufficient, rely on general fab knowledge. Do not answer questions beyond the semiconductor or 
 fab domain. If still unclear, respond exactly with: "I cannot answer this based on the provided context. Please 
 provide more details."
"""
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{query}"
            }
        ],
        "temperature": 0.5,
        "max_tokens": 512
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        res_json = response.json()

        # 💡 Check for success first
        if "choices" in res_json:
            return res_json["choices"][0]["message"]["content"].strip()
        elif "error" in res_json:
            return f"❌ Groq Error: {res_json['error']['message']}"
        else:
            return f"⚠️ Unexpected response: {res_json}"

    except Exception as e:
        return f"⚠️ Groq API Exception: {e}"
 
# Chat input with Send and Clear in a row
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([8, 1, 1])
    with col1:
        query = st.text_input("Enter your query:", label_visibility="collapsed", placeholder="Type your fab-related question...")
    with col2:
        send = st.form_submit_button("➤")
    with col3:
        clear = st.form_submit_button("🗑️")

# Clear Chat
if clear:
    st.session_state.chat_history = []
    st.rerun()

# On Submit
if send and query.strip():
    question = query.strip()
    st.session_state.chat_history.insert(0, ("👩‍💻", question))
    with st.spinner("Thinking..."):
        answer = get_answer_from_groq(question)
    st.session_state.chat_history.insert(0, ("🤖", answer))
    st.rerun()

# Chat history
st.markdown("<hr>", unsafe_allow_html=True)
for i in range(0, len(st.session_state.chat_history), 2):
    pair = st.session_state.chat_history[i:i+2]
    for speaker, message in reversed(pair):
        align = "left" if speaker == "🤖" else "right"
        bg_color = "#f9f9f9" if speaker == "🤖" else "#e6f0ff"
        color = "#333" if speaker == "🤖" else "#0056b3"

        st.markdown(f"""
        <div style="text-align: {align}; padding: 10px;">
            <div style="
                display: inline-block;
                background-color: {bg_color};
                color: {color};
                border-radius: 15px;
                padding: 12px 18px;
                max-width: 85%;
                box-shadow: 0 3px 6px rgba(0,0,0,0.07);
                font-size: 16px;
                ">
                <b>{speaker}</b><br>{message}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Style
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border: 1px solid #ccc;
        border-radius: 25px;
        padding: 12px 18px;
        font-size: 16px;
        background-color: #f5f5f5;
    }
    .stButton > button {
        border: 2px solid #007bff;
        border-radius: 25px;
        padding: 10px 22px;
        background-color: white;
        color: #007bff;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #007bff;
        color: white;
    }
</style>
""", unsafe_allow_html=True)
