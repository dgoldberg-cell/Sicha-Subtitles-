import streamlit as st
import subprocess
import sys
import time

# --- NUCLEAR FIX: FORCE UPDATE THE BRAIN ---
# This forces the server to install the newest Google library 
# right now, ignoring whatever old version is stuck in the cache.
try:
    import google.generativeai as genai
    # Check if version is old, if so, force upgrade
    if int(genai.__version__.split('.')[1]) < 8:
        raise ImportError("Old version detected")
except (ImportError, Exception):
    print("🔄 Force-Updating Google Library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "google-generativeai>=0.8.3"])
    import google.generativeai as genai

import pandas as pd
from docx import Document
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V40 (Auto-Pilot)", layout="wide")
st.title("⚡ Sicha Translator (V40 Auto-Pilot)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    st.caption(f"System Brain Version: {genai.__version__}")
    
    # --- PROMPT ---
    default_prompt = """
# Role
You are a master storyteller translating the Lubavitcher Rebbe’s Sichos.

# RULES
1. **Fidelity:** Translate every thought. Do not summarize.
2. **Structure:** Vertical list. Short lines (3-7 words).
3. **Format:** Use `~` for visual line breaks.
4. **Output Format:** ID | Yiddish | English Subtitle
    """
    with st.expander("Edit Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=200)

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
            # We don't guess the model. We ask Google what is available.
            active_model = None
            try:
                status_box.info("🔍 Scanning for available models...")
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                
                # Priority Logic: Try to find the best one that exists
                if "models/gemini-1.5-flash" in available_models:
                    active_model = "gemini-1.5-flash"
                elif "models/gemini-1.5-pro" in available_models:
                    active_model = "gemini-1.5-pro"
                elif "models/gemini-pro" in available_models:
                    active_model = "gemini-pro"
                else:
                    # If nothing matches, take the first one available
                    if available_models:
                        active_model = available_models[0].replace("models/", "")
                
                if not active_model:
                    st.error("❌ No models found. Your API Key might be invalid or has no access.")
                    st.stop()
                    
                status_box.info(f"✅ locked onto model: {active_model}")
                
            except Exception as e:
                st.error(f"Connection Error: {e}")
                st.stop()

            # --- TRANSLATION ---
            try:
                model = genai.GenerativeModel(active_model)
                full_input = f"{system_prompt}\n\n---\n\nINPUT TEXT:\n{yiddish_text}"
                response = model.generate_content(full_input)
                
                st.session_state['result'] = response.text
                status_box.success("✅ Translation Complete")
                
            except Exception as e:
                status_box.error("❌ Failed during translation.")
                st.error(f"Error: {e}")

    # --- DISPLAY & EXPORT ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        data = []
        for line in raw_text.split('\n'):
            if "|" in line and "ID |" not in line and "---" not in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    data.append({
                        "#": parts[0].strip(),
                        "Yiddish": parts[1].strip(),
                        "English": parts[2].strip().replace("~", "<br>")
                    })
        
        if data:
            df = pd.DataFrame(data)
            for idx, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 4, 4])
                    c1.caption(row['#'])
                    c2.text(row['Yiddish'])
                    c3.markdown(f"**{row['English']}**", unsafe_allow_html=True)
                    st.divider()
            
            # DOCX Export
            doc = Document()
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            for idx, row in df.iterrows():
                cells = table.add_row().cells
                cells[0].text = row['#']
                cells[1].text = row['Yiddish']
                cells[2].text = row['English'].replace("<br>", "\n")
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("Download DOCX", bio.getvalue(), "translation.docx")
        else:
            st.text(raw_text)
