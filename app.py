import os
import pandas as pd
import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

# Page layout
st.set_page_config(page_title="Fab Engineer Assistant 🤖", layout="centered")
st.markdown("<h1 style='text-align: center;'>🛠️ Fab Engineer Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Ask me your tool or fab-related issues. I’ll guide you with steps to troubleshoot them.</p>", unsafe_allow_html=True)

# Load Excel data
df = pd.read_excel("Queries.xlsx")

# Configure Gemini
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("models/gemini-1.5-pro")

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

# Gemini response
def get_answer_from_gemini(query: str) -> str:
    context = get_context(df)
    prompt = f"""
You are a helpful assistant for Fab Engineers, specializing in semiconductor tools, issues, and best practices.

Below is some context from a knowledge base document. Use it when relevant to answer the user's question in **step-by-step**, easy-to-understand language. Do not copy exact lines — explain clearly and naturally.

If the user asks **general questions** about fab processes, semiconductors, machinery, tools, or troubleshooting, you can use your general knowledge even if it’s not found in the context.

If no answer is available or relevant even after that, politely reply:  
"I cannot answer this based on the provided context. Please provide more details."

Context:
{context}

Question:
{query}

Answer (in step-by-step natural language):
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini API Error: {e}"

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
        answer = get_answer_from_gemini(question)
    st.session_state.chat_history.insert(0, ("🤖", answer))
    st.rerun()

# Chat history (latest on top, question first then answer)
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
