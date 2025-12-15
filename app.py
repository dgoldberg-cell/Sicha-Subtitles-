import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V47 (The Scanner)", layout="wide")
st.title("⚡ Sicha Translator (Auto-Detect Mode)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    
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
            status_box.info("🔍 Scanning for available models...")
            
            # --- STEP 1: SCAN FOR MODELS (The Fix) ---
            # We ask Google: "What models do I have?"
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            valid_model_name = None
            
            try:
                list_response = requests.get(list_url)
                if list_response.status_code == 200:
                    models_data = list_response.json()
                    # Look for the first model that supports generating content
                    for m in models_data.get('models', []):
                        if "generateContent" in m.get('supportedGenerationMethods', []):
                            # Prefer Flash or Pro if available, but take anything
                            if "flash" in m['name'] or "pro" in m['name']:
                                valid_model_name = m['name']
                                break
                    
                    # If no preference found, take the first one
                    if not valid_model_name and models_data.get('models'):
                         for m in models_data.get('models', []):
                            if "generateContent" in m.get('supportedGenerationMethods', []):
                                valid_model_name = m['name']
                                break
                else:
                    st.error(f"Could not list models. Error: {list_response.text}")
                    st.stop()
            except Exception as e:
                st.error(f"Network Error during scan: {e}")
                st.stop()
            
            if not valid_model_name:
                st.error("❌ No compatible models found for this API Key.")
                st.stop()

            # --- STEP 2: TRANSLATE USING FOUND MODEL ---
            status_box.info(f"✅ Locked onto: {valid_model_name}")
            
            try:
                # Use the scanned name exactly
                generate_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model_name}:generateContent?key={api_key}"
                
                # Combine prompt and text (Compatibility Mode)
                combined_input = f"{system_prompt}\n\n---\n\nTASK: Translate this text:\n{yiddish_text}"

                headers = {'Content-Type': 'application/json'}
                data = {
                    "contents": [{
                        "parts": [{"text": combined_input}]
                    }],
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
                
                response = requests.post(generate_url, headers=headers, data=json.dumps(data))
                
                if response.status_code == 200:
                    result_json = response.json()
                    try:
                        generated_text = result_json['candidates'][0]['content']['parts'][0]['text']
                        st.session_state['result'] = generated_text
                        status_box.success("✅ Success!")
                    except KeyError:
                        st.error("Model blocked the response (Safety Filters).")
                        st.json(result_json)
                else:
                    st.error(f"Translation Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                st.error(f"Connection Failed: {e}")

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
