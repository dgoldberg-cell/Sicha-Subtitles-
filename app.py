import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V51 (Complete V23)", layout="wide")
st.title("⚡ Sicha Translator (V51 - Complete V23 Restoration)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # --- THE FULL V23 PROMPT (WITH EXAMPLES) ---
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
    * **Split:** Use the tilde symbol `~` to indicate a visual line break inside a single subtitle row.

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

# Few-Shot Examples (V23 Compliant)

### Example A: Brevity & Double Negatives
*Input:*
ניט נאָר וואָס ס'איז ניט קיין שטער, נאָר די רעגירונג העלפט
*Output:*
010 | ניט נאָר וואָס ס'איז ניט קיין שטער | The government will not disturb;~on the contrary, it will help.

### Example B: Active Voice & Visual Balance
*Input:*
ס'איז דאָך ידוע דער וואָרט פון דעם רבי'ן נשמתן עדן
*Output:*
025 | ס'איז דאָך ידוע דער וואָרט פון דעם רבי'ן נשמתן עדן | **My father-in-law, the Rebbe,**~taught the following:

### Example C: Mechanics vs. Meaning & Integration
*Input:*
דער חי"ת איז דאָס די ז' רקיעים... זאגט אים תורת אמת אז "היום" איז דאס "לעשותם"
*Output:*
049 | דער חי"ת איז דאָס די ז' רקיעים... | Since a child can already~see the sky and earth,
050 | זאגט אים תורת אמת אז "היום" איז דאס "לעשותם" | the Torah of Truth informs him~that this world was created for "toil."

# TECHNICAL OUTPUT FORMAT (Required for App)
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

# --- RETRY FUNCTION (The "Battering Ram") ---
def attempt_translation_with_retries(model_name, api_key, full_prompt, max_retries=5):
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
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result_json = response.json()
                try:
                    text = result_json['candidates'][0]['content']['parts'][0]['text']
                    return True, text
                except KeyError:
                    return False, f"Parsed JSON but found no text: {result_json}"
            elif response.status_code == 503:
                st.toast(f"⚠️ Server Busy (Attempt {attempt+1}/{max_retries}). Retrying...", icon="⏳")
                time.sleep(3)
                continue
            elif response.status_code == 404:
                return False, "NOT_FOUND"
            else:
                return False, f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, str(e)
    
    return False, "MAX_RETRIES_EXCEEDED"

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
            
            # Use 2.5 Flash as primary
            target_model = "models/gemini-2.5-flash" 
            
            combined_prompt = f"{system_prompt}\n\n---\n\nTASK: Translate this text:\n{yiddish_text}"

            status_box.info(f"🚀 Processing with V23 Rules + Examples (Model: {target_model})...")
            
            success, result = attempt_translation_with_retries(target_model, api_key, combined_prompt)
            
            if success:
                status_box.success("✅ Connected & Translated!")
                st.session_state['result'] = result
            else:
                if result == "NOT_FOUND":
                     status_box.warning("2.5 Flash not found. Trying backup...")
                     success_bk, result_bk = attempt_translation_with_retries("models/gemini-1.5-flash", api_key, combined_prompt)
                     if success_bk:
                         st.session_state['result'] = result_bk
                         status_box.success("✅ Connected (via Backup)")
                     else:
                         status_box.error(f"❌ Failed: {result}")
                else:
                    status_box.error(f"❌ Failed: {result}")

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
