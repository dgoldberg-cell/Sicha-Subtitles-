import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import pandas as pd

# --- PAGE SETUP (JEM STYLE) ---
st.set_page_config(page_title="JEM Sicha Translator V32", layout="wide")

# --- CUSTOM CSS (JEM.TV THEME) ---
st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    
    /* SIDEBAR BACKGROUND */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* INPUT TEXT AREAS */
    .stTextArea textarea {
        background-color: #21262D;
        color: #E6EDF3;
        border: 1px solid #30363D;
    }
    
    /* BUTTONS (JEM BLUE) */
    div.stButton > button {
        background-color: #2fa4e7; 
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #1d89c4;
        border: 1px solid white;
    }

    /* SUBTITLE CARDS */
    .sub-card {
        background-color: #1F2937;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        border-left: 5px solid #2fa4e7;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .sub-id {
        color: #2fa4e7;
        font-size: 0.8em;
        font-weight: bold;
    }
    .sub-yiddish {
        color: #9CA3AF;
        font-size: 0.9em;
        margin-bottom: 5px;
        font-family: 'Courier New', monospace;
    }
    .sub-english {
        color: #FFFFFF;
        font-size: 1.1em;
        font-weight: 500;
        line-height: 1.4;
    }
    .sub-hebrew {
        color: #FFFFFF;
        font-size: 1.2em;
        font-weight: 500;
        line-height: 1.4;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Sicha Translator")
st.caption("Professional Subtitling AI (JEM Style)")

# --- PROMPTS ---
PROMPT_ENGLISH = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos into English.

# RULES
1. **Fidelity:** Translate every thought. Do not summarize.
2. **Voice:** "Moses reasoned..." / "God who is Infinite..."
3. **Structure:** Short lines (3-7 words). Use `~` for visual line breaks.
4. **Clean:** Remove OCR errors from Yiddish input.

# OUTPUT FORMAT
ID | Yiddish Cleaned | English Subtitle
001 | (Yiddish) | Line one~Line two
"""

PROMPT_HEBREW = """
# Role
You are a master translator adapting the Lubavitcher Rebbe’s Sichos into Torani Hebrew.

# RULES
1. **Quotes:** Keep Loshon HaKodesh quotes EXACT (do not translate).
2. **Aramaic:** Keep quote + brief explanation.
3. **Titles:** "Alter Rebbe" -> "אדמו\"ר הזקן".
4. **Structure:** Short lines. Use `~` for visual line breaks.
5. **Clean:** Remove OCR errors.

# OUTPUT FORMAT (RTL)
ID | Yiddish Cleaned | Hebrew Subtitle
001 | (Yiddish) | שורה ראשונה~שורה שניה
"""

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    
    # LANGUAGE SELECTOR
    target_lang = st.radio("Target Language", ["English (Storyteller)", "Hebrew (Torani)"])
    
    if "English" in target_lang:
        system_prompt = PROMPT_ENGLISH
        is_rtl = False
    else:
        system_prompt = PROMPT_HEBREW
        is_rtl = True
        
    st.divider()
    
    # MODEL SELECTOR
    model_choice = st.selectbox("Model", [
        "gemini-2.0-flash", 
        "gemini-2.5-flash", 
        "gemini-1.5-pro", 
        "gemini-1.5-flash"
    ])

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=600, label_visibility="collapsed")

with col2:
    st.subheader("Output")
    
    if st.button("Translate Now", type="
