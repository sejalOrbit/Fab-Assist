# import pandas as pd
# import re
# import streamlit as st
# from aixplain.factories import ModelFactory
# from rapidfuzz import fuzz

# # ====== CONFIG ======
# ALARM_PATH = "data/Alarm_Manual_Extracted.xlsx"
# GENERAL_PATH = "data/Queries.xlsx"
# MODEL_ID = "669a63646eb56306647e1091"
# TEXT_COLUMNS = ["Alarm Number", "Alarm Message", "Cause", "Recovery"]
# FUZZY_MATCH_THRESHOLD = 65
# # =====================

# # Initialize model
# model = ModelFactory.get(MODEL_ID)

# # --- Utils ---
# def clean_text(val):
#     if pd.isna(val):
#         return ""
#     val = re.sub(r"[^\w\s]", " ", str(val))
#     val = re.sub(r"\s+", " ", val)
#     return val.strip().lower()

# @st.cache_data
# def load_alarm_data():
#     df = pd.read_excel(ALARM_PATH)
#     for col in TEXT_COLUMNS:
#         if col in df.columns:
#             df[col] = df[col].astype(str).apply(clean_text)
#     return df

# @st.cache_data
# def load_query_data():
#     df = pd.read_excel(GENERAL_PATH)
#     for col in df.columns:
#         df[col] = df[col].astype(str).apply(clean_text)
#     return df

# def preprocess_user_input(query):
#     query = re.sub(r"(got (the )?message|what alarm is.*|error.*|alert.*|message is|received)", "", query, flags=re.IGNORECASE)
#     return clean_text(query)

# def fuzzy_search(df, query):
#     query = preprocess_user_input(query)
#     if not query:
#         return pd.DataFrame()

#     num_match = re.findall(r"\b\d{2,5}\b|\b[a-f0-9]{4}\b", query)
#     if num_match:
#         for num in num_match:
#             exact = df[df["Alarm Number"].str.contains(num.lower(), na=False)]
#             if not exact.empty:
#                 return exact

#     row_scores = []
#     for idx, row in df.iterrows():
#         combined = " ".join(row[col] for col in TEXT_COLUMNS if col in row)
#         score = fuzz.partial_ratio(query, combined)
#         if score >= FUZZY_MATCH_THRESHOLD:
#             row_scores.append((idx, score))

#     row_scores.sort(key=lambda x: x[1], reverse=True)
#     return df.loc[[i for i, _ in row_scores]]

# def build_context_from_row(row):
#     return "\n".join([f"{col}: {row[col]}" for col in TEXT_COLUMNS if col in row and pd.notna(row[col])])

# def flatten_context(df):
#     return "\n".join(df.astype(str).fillna("").values.flatten())

# def build_prompt(query, context):
#     return f"""You are a fab engineering assistant.

# Respond briefly and clearly in 2–4 sentences. Do not repeat the alarm text. Just explain the cause and what to do, concisely.

# --- Alarm Info ---
# {context}

# --- Question ---
# {query}

# --- Answer ---"""

# def build_general_prompt(query, context):
#     return f"""
# You are a fab assistant for semiconductor engineers. Use the following instructions to answer queries based on the context provided.

# 🎯 Instructions:
# - Answer clearly, with **short, and maximum 5 step-by-step points**
# - Use plain language — avoid chatty or reflective tone
# - Don’t use "I see", "Let me", or long explanations
# - **Max: 4 bullet points**
# - No intro, no summary, no repeats of the question, only the answer

# 🧠 Use provided context. If not enough info, use general fab knowledge.
# If still unclear, say:
# "I cannot answer this based on the provided context. Please provide more details."

# Context:
# {context}

# Question:
# {query}

# Answer:
# """

# def query_model(prompt):
#     try:
#         result = model.run({
#             "text": [{"role": "user", "content": prompt}],
#             "temperature": 0.2,
#             "max_tokens": 500
#         })

#         details = result.get("details", [])
#         if details and "message" in details[0]:
#             return details[0]["message"].get("content", "[⚠️ No content found in message]").strip()

#         output = result.get("data", "").strip()
#         return output or "[⚠️ No content returned from model.]"

#     except Exception as e:
#         return f"⚠️ Model Error: {e}"

# # --- Streamlit UI ---
# st.set_page_config(page_title="Fab-Assist", layout="centered")
# st.markdown("<h1 style='text-align: center;'>🛠️ Fab-Assist</h1>", unsafe_allow_html=True)
# st.markdown("<p style='text-align: center;'>Use the toggle to switch between alarm lookups and general fab troubleshooting.</p>", unsafe_allow_html=True)

# # Section Selector
# query_type = st.radio(
#     "Choose Query Type:",
#     ["🚨 Alarm Manual", "🔧 General Fab Queries"],
#     horizontal=True
# )

# # History Init
# if "history" not in st.session_state:
#     st.session_state.history = []

# # Input Form
# with st.form(key="fab_query_form"):
#     user_input = st.text_input("🔎 Enter your query", placeholder="e.g. 'Got alarm ARM P/CW. P. Wafer Lost'").strip()
#     submitted = st.form_submit_button("Get Answer")

# if submitted and user_input:
#     entries = []

#     if query_type == "🚨 Alarm Manual":
#         alarm_df = load_alarm_data()
#         matches = fuzzy_search(alarm_df, user_input)

#         if matches.empty:
#             entries.append({
#                 "question": user_input,
#                 "results": [],
#                 "warning": f"No alarms found matching: '{user_input}'"
#             })
#         else:
#             for _, row in matches.iterrows():
#                 context = build_context_from_row(row)
#                 prompt = build_prompt(user_input, context)
#                 with st.spinner("Thinking..."):
#                     answer = query_model(prompt)

#                 entries.append({
#                     "question": user_input,
#                     "context": context,
#                     "answer": answer,
#                     "type": "Alarm"
#                 })

#     else:  # General Fab Queries
#         queries_df = load_query_data()
#         context = flatten_context(queries_df)
#         prompt = build_general_prompt(user_input, context)

#         with st.spinner("Thinking..."):
#             answer = query_model(prompt)

#         entries.append({
#             "question": user_input,
#             "context": "[General fab troubleshooting context]",
#             "answer": answer,
#             "type": "General"
#         })

#     st.session_state.history.append(entries)

# # --- Display History ---
# if st.session_state.history:
#     st.markdown("#### Previous Queries")
#     for group in reversed(st.session_state.history):
#         for entry in group:
#             query_label = "🔧 General Query" if entry.get("type") == "General" else "🚨 Alarm Query"
#             st.markdown(f"**{query_label}**")
#             st.markdown(f"##### Question :\n> {entry['question']}", unsafe_allow_html=True)

#             if "warning" in entry:
#                 st.warning(entry["warning"])
#             else:
#                 st.code(entry["context"], language="markdown")
#                 st.markdown("##### Bot Suggestions")
#                 st.markdown(entry["answer"], unsafe_allow_html=True)

#             st.markdown("---")

# # --- Styling ---
# st.markdown("""
# <style>
#     .stTextInput input {
#         padding: 10px;
#         border-radius: 8px;
#         font-size: 16px;
#         background-color: #f9f9f9;
#     }
#     .stButton>button {
#         background-color: #007BFF;
#         color: white;
#         border-radius: 8px;
#         font-weight: bold;
#     }
#     .stButton>button:hover {
#         background-color: #0056b3;
#     }
# </style>
# """, unsafe_allow_html=True)
import os
import pandas as pd
import re
import streamlit as st
from rapidfuzz import fuzz
from aixplain.factories import ModelFactory

# ====== CONFIG ======
ALARM_PATH = "data/Alarm_Manual_Extracted.xlsx"
GENERAL_PATH = "data/Queries.xlsx"
TEXT_COLUMNS = ["Alarm Number", "Alarm Message", "Cause", "Recovery"]
FUZZY_MATCH_THRESHOLD = 65
MODEL_ID = "669a63646eb56306647e1091"
# =====================
# --- Streamlit UI ---
st.set_page_config(page_title="Fab-Assist", layout="centered")
st.markdown("<h1 style='text-align: center;'>🛠️ Fab-Assist Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Ask fab-related or alarm troubleshooting questions below. I'll guide you with steps.</p>", unsafe_allow_html=True)
# --- Initialize Aixplain Model ---
model = ModelFactory.get(MODEL_ID)

# --- Text Processing ---
def clean_text(val):
    if pd.isna(val):
        return ""
    val = re.sub(r"[^\w\s]", " ", str(val))
    val = re.sub(r"\s+", " ", val)
    return val.strip().lower()

def preprocess_user_input(query):
    query = re.sub(r"(got (the )?message|what alarm is.*|error.*|alert.*|cause.*|recover.*|recovery.*|number.*|message is|received)", "", query, flags=re.IGNORECASE)
    return clean_text(query)
# --- Load Data ---
@st.cache_data
def load_alarm_data():
    df = pd.read_excel(ALARM_PATH)
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(clean_text)
    return df

@st.cache_data
def load_query_data():
    df = pd.read_excel(GENERAL_PATH)
    for col in df.columns:
        df[col] = df[col].astype(str).apply(clean_text)
    return df

alarm_df = load_alarm_data()
query_df = load_query_data()



# --- Fuzzy Search ---
def fuzzy_search(df, query):
    query = preprocess_user_input(query)
    if not query:
        return pd.DataFrame()

    num_match = re.findall(r"\b\d{2,5}\b|\b[a-f0-9]{4}\b", query)
    if num_match:
        for num in num_match:
            exact = df[df["Alarm Number"].str.contains(num.lower(), na=False)]
            if not exact.empty:
                return exact

    row_scores = []
    for idx, row in df.iterrows():
        combined = " ".join(row[col] for col in TEXT_COLUMNS if col in row)
        score = fuzz.partial_ratio(query, combined)
        if score >= FUZZY_MATCH_THRESHOLD:
            row_scores.append((idx, score))

    row_scores.sort(key=lambda x: x[1], reverse=True)
    return df.loc[[i for i, _ in row_scores]]

# --- Context Builders ---
def build_alarm_context(row):
    return "\n".join([f"{col}: {row[col]}" for col in TEXT_COLUMNS if col in row and pd.notna(row[col])])

def flatten_general_context(df):
    return "\n".join(df.astype(str).fillna("").values.flatten())

general_context = flatten_general_context(query_df)

# --- Prompt Builders ---
def build_alarm_prompt(query, context):
    return f"""You are a fab engineering assistant providing alarm troubleshooting help.

The following information is from the Alarm Manual. It includes:
- Alarm Number: Unique code for the alarm
- Alarm Message: The system's description of the alarm
- Cause: The likely reason the alarm occurred
- Recovery: Recommended actions to resolve the alarm

Your task:
✔ Respond in 2-4 short, clear sentences  
✔ Summarize the likely cause and the recommended recovery actions  
✔ Use plain, technician-friendly language — avoid copying text word-for-word from the manual  
✔ Focus on actionable steps like "Check", "Replace", "Verify", "Restart"  
✔ Do not repeat the alarm message or unnecessary background  

--- Alarm Manual Info ---
{context}

--- Question ---
{query}

--- Answer ---
"""


def build_general_prompt(query, context):
    return f"""
You are a fab assistant helping engineers troubleshoot tool, fab, or process issues.

The following context contains real-world issues and their corresponding corrective actions from fab operations. Use this information to guide your response.

🎯 Instructions:
- Provide a clear, actionable answer in up to 5 bullet points  
- Use simple, technician-friendly language  
- Focus on practical next steps (e.g., "Check", "Replace", "Calibrate", "Purge", etc.)  
- Do not repeat the issue description word-for-word  
- No unnecessary introduction or summary  
- If context is insufficient, rely on general fab knowledge  
- If still unclear, say: "I cannot answer this based on the provided context. Please provide more details."  

--- Fab Issue & Action Data ---
{context}

--- Question ---
{query}

--- Answer ---
"""


# --- Model Call using Aixplain ---
def query_model(prompt):
    try:
        result = model.run({
            "text": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 500
        })

        details = result.get("details", [])
        if details and "message" in details[0]:
            return details[0]["message"].get("content", "[⚠️ No content found in message]").strip()

        output = result.get("data", "").strip()
        return output or "[⚠️ No content returned from model.]"

    except Exception as e:
        return f"⚠️ Model Error: {e}"

# --- Intent Detection ---
def is_alarm_query(query):
    query = query.lower()

    # Hard triggers - always treated as alarm lookup
    hard_triggers = ["alarm number", "alarm message", "cause", "recovery", "mapping data"]

    # Soft indicators - suggest alarm lookup but can fallback
    soft_indicators = [
        "alarm", "error code", "interlock", "shutdown", 
        "wafer slot", "cassette", "wafer lost", "arm", "p/cw", 
        "vacuum", "pressure", "cp fail", "etch rate", "lift pin", "rf error"
    ]

    # If hard triggers present, force alarm lookup
    if any(kw in query for kw in hard_triggers):
        return True

    # Check for typical alarm number patterns
    alarm_number_match = re.search(r"\b\d{2,5}\b|\b[a-f0-9]{4}\b", query)
    if alarm_number_match:
        return True

    # If soft indicators present, treat as alarm query
    if any(kw in query for kw in soft_indicators):
        return True

    return False





if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Chat Form ---
with st.form(key="chat_form", clear_on_submit=True):
    query = st.text_input("🔎 Enter your question", placeholder="e.g. 'Got alarm 0002 Mapping Data Error' or 'Tool not loading wafers'")
    submit = st.form_submit_button("Ask")

# --- Clear Chat Button ---
if st.button("🗑️ Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()

# --- Chat Logic ---
if submit and query.strip():
    user_query = query.strip()
    st.session_state.chat_history.insert(0, ("👨‍🔧", user_query))

    with st.spinner("Thinking..."):
        if is_alarm_query(user_query):
            matches = fuzzy_search(alarm_df, user_query)
            if not matches.empty:
                context = build_alarm_context(matches.iloc[0])
                prompt = build_alarm_prompt(user_query, context)
                answer = query_model(prompt)
            else:
                answer = "I cannot find relevant alarm details for this. Please verify the alarm code or description."
        else:
            prompt = build_general_prompt(user_query, general_context)
            answer = query_model(prompt)

    st.session_state.chat_history.insert(0, ("🤖", answer))
    st.rerun()

# --- Display Chat History ---
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

# --- Styling ---
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
