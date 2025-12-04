import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V29 (Storyteller Core)", layout="wide")
st.title("⚡ Sicha Translator (Storyteller Core V29)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    
    api_key = st.text_input("Enter Google API Key", type="password")
    
    st.divider()
    st.info("ℹ️ **Auto-Pilot Active:** System will find the best model for your key.")

    # --- THE V23 MASTER PROMPT (THE "GOOD" ONE) ---
    # We use this EXACT text because you confirmed it translates best.
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos. Your goal is to produce **narrative, high-impact English** that focuses on the *character's voice* and *intended meaning* while adhering to strict video-subtitle standards.

# MODULE A: FIDELITY (The "Zero-Loss" Rule)
* **CRITICAL:** Do not summarize. Every distinct thought in the Yiddish must have a corresponding English phrase.
* **Action:** Change structure for flow, but never remove content.

# MODULE B: NARRATIVE VOICE & THEOLOGY
### 1. VOICE ATTRIBUTION
* **Action:** Insert tags to describe internal thought processes.
* *Input:* "If the other person..." -> *Output:* "**Moses reasoned**, 'If another person...'"

### 2. PHENOMENON OVER LABEL
* **Action:** Describe the effect/meaning, not the technical label.
* *Input:* "Nimna Hanimnaos" -> *Output:* "**God, who is Infinite, and therefore contains the finite.**"

### 3. THE "QUOTE CONTEXT" RULE
* **Liturgy:** Translate objects of study literally ("**Hear O Israel...**").
* **Prooftext:** Translate the point of the quote ("**Man was born to toil**").
* **Integration:** Weave quotes into grammar; avoid colons.

# MODULE C: CULTURAL & LINGUISTIC TRANSLATION
### 4. CONCEPT OVER ETYMOLOGY (The "Adam" Rule)
* **Action:** Translate the *implication*. *Adam* -> "**Created in God's image.**"

### 5. MECHANICS VS. MEANING
* **Action:** If text uses mechanics (Gematria/Letters) to explain a concept, translate the **concept**.
* *Input:* "Ches is 7 heavens..." -> *Output:* "**Since a child sees the heavens and earth...**"

### 6. RELATIONAL TITLES
* **Action:** *Der Rebbe (Nishmaso Eden)* -> "**My father-in-law, the Rebbe.**"

# MODULE D: VISUAL STRUCTURE & RHYTHM
### 7. VERTICAL RHYTHM & BALANCE
* **Logic:** Subtitles must be readable in seconds.
* **Action:**
    * **Length:** Max 40 characters (approx 3-7 words) per line.
    * **Balance:** If using 2 lines, keep them roughly equal in length.
    * **Grammatical Breaks:** Never break a line between an adjective and noun, or preposition and object.

### 8. LOGICAL BRIDGING
* **Action:** Insert connectors: **"But first," "However," "Simply put."**

# MODULE E: SYNTAX & BREVITY (The "Manual" Rules)
### 9. ACTIVE VOICE CONVERSION
* **Logic:** Passive voice wastes space and time.
* **Action:** Convert to Active.
    * *Input:* "It is believed by many..." -> *Output:* "**Many believe...**"

### 10. POSITIVE PHRASING
* **Logic:** Negative phrasing ("Place we hadn't been") is wordy.
* **Action:** Convert to Positive ("**A new place**").

### 11. THE DOUBLE-NEGATIVE FIX
* **Logic:** Double negatives ("Not only will they not disturb") are confusing on screen.
* **Action:** Flip to Positive + Contrast.
    * *Input:* "Not only will they not disturb..." -> *Output:* "**The government will not disturb; / on the contrary, it will help.**"

### 12. INTRO REMOVAL
* **Action:** Remove conversational filler.
    * *Input:* "I would like to know if you are coming." -> *Output:* "**Are you coming?**"
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
    st.subheader("Output")
    
    if st.button("Translate (Storyteller)", type="primary"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            
            # --- AUTO-PILOT LOOP ---
            success = False
            status_box = st.empty()
            genai.configure(api_key=api_key)

            # --- DYNAMIC INSTRUCTIONS (THE SECRET SAUCE) ---
            # We append the technical rules HERE, so they don't mess up the creative prompt.
            final_instruction = system_prompt + """
            
            # FORMATTING INSTRUCTIONS (CRITICAL)
            1. **Output Format:** Provide a Pipe-Separated Table with 3 columns:
               ID | Yiddish Cleaned | English Subtitle
            2. **Yiddish Column:** You MUST clean the Yiddish text (remove OCR errors, brackets, artifacts).
            3. **English Column:** Use the tilde symbol `~` to indicate a visual line break inside the English text (e.g., "The light shines~ever the brighter").
            4. **Completeness:** Translate EVERY sentence. Do not skip.
            """

            for model_name in MODEL_PRIORITY:
                try:
                    status_box.caption(f"🚀 Trying model: **{model_name}**...")
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=final_instruction)
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
            if "|" in line and "ID |" not in line and "---" not in line: 
                parts = line.split('|')
                if len(parts) >= 3:
                    row_id = parts[0].strip()
                    yiddish = parts[1].strip()
                    # Convert ~ to HTML Break for Screen
                    english_raw = parts[2].strip()
                    english_html = english_raw.replace("~", "<br>") 
                    data.append({"#": row_id, "Yiddish": yiddish, "English": english_html, "English_Raw": english_raw})
        
        if data:
            df = pd.DataFrame(data)
            
            # 1. DISPLAY TABLE (Clean & Storyteller Style)
            st.markdown(
                df[['#', 'Yiddish', 'English']].to_html(escape=False, index=False), 
                unsafe_allow_html=True
            )
            
            st.divider()
            
            # 2. CREATE WORD DOC (Clean)
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
            # Fallback if table parsing fails (rare)
            st.warning("Could not format as table. Raw output:")
            st.text(raw_text)
