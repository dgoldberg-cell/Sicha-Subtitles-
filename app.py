import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V27 (Smart Table)", layout="wide")
st.title("⚡ Sicha Translator (Clean Table V27)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    
    api_key = st.text_input("Enter Google API Key", type="password")
    
    st.divider()
    st.info("ℹ️ **Auto-Pilot Active:** System will find the best model for your key.")

    # --- THE V27 MASTER PROMPT (JSON/STRUCTURED) ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: THE "JANITOR" (Source Cleaning)
* **CRITICAL:** When outputting the Yiddish Source column, you must CLEAN the text.
* **Remove:** Random symbols (??, *, #), OCR artifacts, and parenthetical interruptions.
* **Retain:** The actual spoken words.

# MODULE B: FIDELITY (The "Zero-Loss" Rule)
* **CRITICAL:** Do not summarize. Every distinct thought in the Yiddish must have a corresponding English phrase.

# MODULE C: NARRATIVE VOICE & THEOLOGY
* **Voice Attribution:** Insert tags: "**Moses reasoned**, 'If another person...'"
* **Phenomenon:** Describe effect. "Nimna Hanimnaos" -> "**God, who is Infinite, and therefore contains the finite.**"
* **Quotes:** Liturgy = Literal. Prooftext = Meaning.

# MODULE D: CULTURAL TRANSLATION
* *Adam* -> "**Created in God's image.**"
* *Der Rebbe* -> "**My father-in-law, the Rebbe.**"

# MODULE E: VISUAL STRUCTURE (The "Tilde" Rule)
* **CRITICAL:** Subtitles must be readable in seconds.
* **Action:** Break English text into short lines (3-7 words max).
* **Format:** Use the tilde symbol `~` to indicate a visual line break inside a subtitle.
    * *Bad:* "The government will not disturb; on the contrary, it will help."
    * *Good:* "The government will not disturb;~on the contrary, it will help."

# MODULE F: SYNTAX
* Active Voice. No Intro Fillers.

# OUTPUT FORMAT RULE (CRITICAL)
Provide the output as a Pipe-Separated List (CSV style) with exactly 3 columns:
ID | Yiddish Cleaned | English Subtitle

Example:
001 | Clean Yiddish text here | English text line one~English text line two
002 | Next Yiddish text | Next English translation
    """
    
    with st.expander("Advanced: Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=300)

# --- MODEL PRIORITY LIST ---
MODEL_PRIORITY = [
    "gemini-2.5-flash",          
    "gemini-2.0-flash",          
    "gemini-1.5-pro",            
    "gemini-1.5-flash",          
    "gemini-1.5-flash-8b",       
    "gemini-1.5-pro-001"         
]

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=600)

with col2:
    st.subheader("Output (Preview)")
    
    if st.button("Translate", type="primary"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            
            # --- AUTO-PILOT LOOP ---
            success = False
            status_box = st.empty()
            genai.configure(api_key=api_key)

            for model_name in MODEL_PRIORITY:
                try:
                    status_box.caption(f"🚀 Trying model: **{model_name}**...")
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                    response = model.generate_content(yiddish_text)
                    st.session_state['result'] = response.text
                    st.session_state['used_model'] = model_name
                    success = True
                    status_box.success(f"✅ Success! Used model: **{model_name}**")
                    break 
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    time.sleep(0.5)

            if not success:
                st.error("❌ All models failed. Please check your API Key.")

    # --- RESULT PROCESSING ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        
        # Parse the Pipe-Separated Text into a Dataframe
        data = []
        for line in raw_text.split('\n'):
            if "|" in line and "ID |" not in line and "---" not in line: # Skip headers/garbage
                parts = line.split('|')
                if len(parts) >= 3:
                    row_id = parts[0].strip()
                    yiddish = parts[1].strip()
                    # Convert ~ to HTML Break for Screen, Keep ~ for logic
                    english_raw = parts[2].strip()
                    english_html = english_raw.replace("~", "<br>") 
                    data.append({"#": row_id, "Yiddish": yiddish, "English": english_html, "English_Raw": english_raw})
        
        if data:
            df = pd.DataFrame(data)
            
            # 1. DISPLAY TABLE (With HTML rendering for breaks)
            st.markdown(
                df[['#', 'Yiddish', 'English']].to_html(escape=False, index=False), 
                unsafe_allow_html=True
            )
            
            st.divider()
            
            # 2. CREATE WORD DOC (With Real Line Breaks)
            doc = Document()
            doc.add_heading(f"Translation ({st.session_state.get('used_model')})", 0)
            
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '#'
            hdr_cells[1].text = 'Yiddish'
            hdr_cells[2].text = 'English'
            
            for index, row in df.iterrows():
                row_cells = table.add_row().cells
                row_cells[0].text = row['#']
                row_cells[1].text = row['Yiddish']
                # Replace Tilde with Real Line Break in Word
                clean_english = row['English_Raw'].replace("~", "\n")
                row_cells[2].text = clean_english

            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="Download Formatted Word Doc",
                data=bio.getvalue(),
                file_name="translation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Translation complete, but table parsing failed. Raw output below:")
            st.text(raw_text)
