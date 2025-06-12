import pandas as pd
import re
import streamlit as st
from aixplain.factories import ModelFactory
from rapidfuzz import fuzz

# ====== CONFIG ======
EXCEL_PATH = "data/Alarm_Manual_Extracted.xlsx"
MODEL_ID = "669a63646eb56306647e1091"
TEXT_COLUMNS = ["Alarm Number", "Alarm Message", "Cause", "Recovery"]
FUZZY_MATCH_THRESHOLD = 65
# =====================

# Initialize model
model = ModelFactory.get(MODEL_ID)

# --- Utilities ---
def clean_text(val):
    if pd.isna(val):
        return ""
    val = re.sub(r"[^\w\s]", " ", str(val))  # remove punctuation
    val = re.sub(r"\s+", " ", val)  # normalize spaces
    return val.strip().lower()

@st.cache_data
def load_excel_data(file_path):
    df = pd.read_excel(file_path)
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(clean_text)
    return df

def preprocess_user_input(query):
    # Remove filler words/phrases
    query = re.sub(r"(got (the )?message|what alarm is.*|error.*|alert.*|message is|received)", "", query, flags=re.IGNORECASE)
    return clean_text(query)

def fuzzy_search(df, query):
    query = preprocess_user_input(query)
    if not query:
        return pd.DataFrame()

    # Check for numeric match (alarm number)
    num_match = re.findall(r"\b\d{2,5}\b|\b[a-f0-9]{4}\b", query)
    if num_match:
        for num in num_match:
            exact = df[df["Alarm Number"].str.contains(num.lower(), na=False)]
            if not exact.empty:
                return exact

    # Otherwise, fuzzy match
    row_scores = []
    for idx, row in df.iterrows():
        combined = " ".join(row[col] for col in TEXT_COLUMNS if col in row)
        score = fuzz.partial_ratio(query, combined)
        if score >= FUZZY_MATCH_THRESHOLD:
            row_scores.append((idx, score))

    row_scores.sort(key=lambda x: x[1], reverse=True)
    return df.loc[[i for i, _ in row_scores]]

def build_context_from_row(row):
    return "\n".join([f"{col}: {row[col]}" for col in TEXT_COLUMNS if col in row and pd.notna(row[col])])

def build_prompt(query, context):
    return f"""You are a fab engineering assistant.

Respond briefly and clearly in 2–4 sentences. Do not repeat the alarm text. Just explain the cause and what to do, concisely.

--- Alarm Info ---
{context}

--- Question ---
{query}

--- Answer ---"""

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

# --- Streamlit UI ---
st.set_page_config(page_title="Fab-Assist", layout="centered")
st.markdown("<h1 style='text-align: center;'>🛠️ Fab-Assist</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Type anything about an alarm (number, message, cause, etc.) and get help.</p>", unsafe_allow_html=True)

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# User input form
with st.form(key="alarm_query_form"):
    user_input = st.text_input("🔎 Describe the alarm or ask a question", placeholder="e.g. 'got the message ARM P/CW. P. Wafer Lost'").strip()
    submitted = st.form_submit_button("Get Answer")

if submitted and user_input:
    df = load_excel_data(EXCEL_PATH)
    matches = fuzzy_search(df, user_input)

    entries = []

    if matches.empty:
        entries.append({
            "question": user_input,
            "results": [],
            "warning": f"No alarms found matching: '{user_input}'"
        })
    else:
        for _, row in matches.iterrows():
            context = build_context_from_row(row)
            prompt = build_prompt(user_input, context)
            with st.spinner("Thinking..."):
                answer = query_model(prompt)

            entries.append({
                "question": user_input,
                "context": context,
                "answer": answer
            })

    st.session_state.history.append(entries)

# Display query history
if st.session_state.history:
    st.markdown("#### Previous Queries")
    for i, group in enumerate(st.session_state.history[::-1], 1):
        for entry in group:
            st.markdown(f"##### Question :\n> {entry['question']}", unsafe_allow_html=True)

            if "warning" in entry:
                st.warning(entry["warning"])
            else:
                st.code(entry["context"], language="markdown")
                st.markdown("##### Bot Suggestions")
                st.markdown(entry["answer"], unsafe_allow_html=True)

            st.markdown("---")

# --- Custom Styling ---
st.markdown("""
<style>
    .stTextInput input {
        padding: 10px;
        border-radius: 8px;
        font-size: 16px;
        background-color: #f9f9f9;
    }
    .stButton>button {
        background-color: #007BFF;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)
