import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V48 (Auto-Backup)", layout="wide")
st.title("⚡ Sicha Translator (V48 - The Relay System)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    st.caption("System: Direct API + Auto-Fallback Logic")

    # --- THE MASTER V24 PROMPT ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: THE "JANITOR" (Source Cleaning)
* **CRITICAL:** When outputting the Yiddish Source column, you must CLEAN the text.
* **Remove:** Random symbols (??, *, #), OCR artifacts.
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
* **Balance:** Two lines should be visually equal.
* **Split:** Use the tilde symbol `~` to indicate a visual line break inside a single subtitle row.

### 7. LOGICAL BRIDGING
* **Action:** Insert connectors: **"But first," "However."**

# MODULE F: SYNTAX
### 8. ACTIVE VOICE & POSITIVE PHRASING
* Convert Passive -> Active.
* Convert Double Negative -> Positive + Contrast.

# OUTPUT FORMAT RULE (Strict Pipe-List)
Provide the output as a simple list with 3 columns separated by pipes (|).
Do NOT use Markdown Table syntax. Just raw lines.

Format:
ID | Yiddish Cleaned | English Subtitle

Example:
001 | (Yiddish Text) | English line one~English line two
002 | (Yiddish Text) | Next English line
    """
    
    with st.expander("Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=400)

# --- FUNCTIONS ---
def try_model(model_name, api_key, full_prompt):
    """Tries to translate using a specific model. Returns (Success, Text/Error)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            result_json = response.json()
            try:
                text = result_json['candidates'][0]['content']['parts'][0]['text']
                return True, text
            except KeyError:
                return False, f"Parsed JSON but found no text (Safety Block?): {result_json}"
        elif response.status_code == 503:
            return False, "OVERLOADED"
        elif response.status_code == 404:
            return False, "NOT_FOUND"
        else:
            return False, f"Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, str(e)

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
            
            # --- THE RELAY RACE ---
            # We list models in order of preference.
            # 1. Flash 1.5 (Fastest, Stable)
            # 2. Pro 1.5 (Smartest)
            # 3. Flash 2.5 (Newest, but overloaded)
            # 4. Gemini Pro (Old Reliable)
            
            # Note: We prioritize 1.5 Flash now because 2.5 is crashing.
            candidate_models = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-2.5-flash",
                "models/gemini-pro"
            ]
            
            success = False
            final_text = ""
            
            combined_prompt = f"{system_prompt}\n\n---\n\nTASK: Translate this text:\n{yiddish_text}"

            for model in candidate_models:
                status_box.info(f"🔄 Trying model: {model}...")
                is_ok, result = try_model(model, api_key, combined_prompt)
                
                if is_ok:
                    status_box.success(f"✅ Success using {model}!")
                    st.session_state['result'] = result
                    success = True
                    break # Stop the loop, we won!
                else:
                    # If it failed, show why and continue loop
                    if result == "OVERLOADED":
                        st.warning(f"⚠️ {model} is overloaded. Switching to backup...")
                    elif result == "NOT_FOUND":
                        st.warning(f"⚠️ {model} not found for this key. Switching...")
                    else:
                        st.warning(f"⚠️ {model} failed ({result}). Switching...")
                    time.sleep(1) # Brief pause before next try

            if not success:
                status_box.error("❌ All models failed. Please check your API Key or try again later.")

    # --- RESULT DISPLAY ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        
        # Parse
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
        
        # Display Cards
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
        
        # Fallback View
        with st.expander("View Raw Output"):
            st.text(raw_text)
