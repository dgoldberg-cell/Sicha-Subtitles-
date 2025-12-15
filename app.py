import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V42 (Complete)", layout="wide")
st.title("⚡ Sicha Translator (V42 - Complete)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    
    # --- THE MASTER V24 PROMPT (RESTORED) ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: THE "JANITOR" (Source Cleaning)
* **CRITICAL:** When outputting the Yiddish Source column, you must CLEAN the text.
* **Remove:** Random symbols (??, *, #), OCR artifacts, and parenthetical interruptions that are not part of the sentence flow.
* **Retain:** The actual spoken words.

# MODULE B: FIDELITY (The "Zero-Loss" Rule)
* **CRITICAL:** Do not summarize. Every distinct thought in the Yiddish must have a corresponding English phrase.

# MODULE C: NARRATIVE VOICE & THEOLOGY
### 1. VOICE ATTRIBUTION
* **Action:** Insert tags: "**Moses reasoned**, 'If another person...'"

### 2. PHENOMENON OVER LABEL
* **Action:** Describe effect. "Nimna Hanimnaos" -> "**God, who is Infinite, and therefore contains the finite.**"

### 3. QUOTE CONTEXT
* **Liturgy:** Literal ("**Hear O Israel...**").
* **Prooftext:** Meaning ("**Man was born to toil**").

# MODULE D: CULTURAL TRANSLATION
### 4. CONCEPT OVER ETYMOLOGY
* *Adam* -> "**Created in God's image.**"
* *Aleph-Beis mechanics* -> Translate the **concept** the letters represent.

### 5. RELATIONAL TITLES
* *Der Rebbe* -> "**My father-in-law, the Rebbe.**"

# MODULE E: VISUAL STRUCTURE
### 6. VERTICAL RHYTHM
* **Length:** Max 40 chars (3-7 words) per line.
* **Balance:** Two lines should be visually equal (pyramid/rectangle).
* **Split:** Use the tilde symbol `~` to indicate a visual line break inside a single subtitle row.

### 7. LOGICAL BRIDGING
* **Action:** Insert connectors: **"But first," "However."**

# MODULE F: SYNTAX (The Manual)
### 8. ACTIVE VOICE & POSITIVE PHRASING
* Convert Passive -> Active.
* Convert Double Negative -> Positive + Contrast.

# OUTPUT FORMAT RULE (Strict Pipe-List)
Provide the output as a simple list with 3 columns separated by pipes (|).
Do NOT use Markdown Table syntax (no dashes ---). Just raw lines.

Format:
ID | Yiddish Cleaned | English Subtitle

Example:
001 | (Yiddish Text) | English line one~English line two
002 | (Yiddish Text) | Next English line
    """
    
    with st.expander("Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=400)

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input")
    yiddish_text = st.text_area("Paste text here...", height=600)

with col2:
    st.subheader("Output")
    
    if st.button("Translate", type="primary"):
        if not api_key:
            st.error("Please enter your API Key.")
        elif not yiddish_text:
            st.warning("Please paste text.")
        else:
            status_box = st.empty()
            genai.configure(api_key=api_key)
            
            # --- AUTO-PILOT MODEL SELECTION ---
            active_model = None
            try:
                status_box.info("🔍 Scanning for available models...")
                available_models = []
                # Simple check for standard models
                candidates = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
                
                # We try to instantiate them to see if they work with your key
                for c in candidates:
                    try:
