import streamlit as st
import requests
import json
import pandas as pd
from docx import Document
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V54 (Aggressive Segmentation)", layout="wide")
st.title("⚡ Sicha Translator (V54 - Aggressive Segmentation)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # --- THE NEW V54 PROMPT (Your Exact Specs) ---
    default_prompt = """
# Role
You are a master subtitler adapting the Lubavitcher Rebbe’s Sichos. Your goal is to produce **narrative, high-impact English** that captures the speaker's voice while adhering to strict video-subtitle standards.

# MODULE A: PERSPECTIVE (The "No Narrator" Rule)
* **CRITICAL:** These are subtitles for the person on screen.
* **FORBIDDEN:** Never write "The Rebbe explains," "He emphasizes," "The speaker continues," or "They teach us."
* **ACTION:** Translate ONLY what is said in the first person (I/We).
    * *Bad:* "The Rebbe explains that the Alter Rebbe was released..."
    * *Good:* "Although **the Alter Rebbe** was released..."

# MODULE B: FIDELITY & AGGRESSIVE SEGMENTATION
* **The "Zero-Loss" Rule:** Do not summarize. Every distinct thought in the Yiddish must have a corresponding English phrase.
* **The "Short-Burst" Rule:** Do not try to fit a long Yiddish sentence into one subtitle. **Break long complex sentences into 2, 3, or even 4 separate, short subtitle events.**
    * *Logic:* Better to have 3 short, readable subtitles than 1 long, crowded one.

# MODULE C: NARRATIVE VOICE & THEOLOGY
### 1. VOICE ATTRIBUTION (Internal Dialogue)
* **Action:** Insert tags to describe internal thought processes of *characters in the story* (not the speaker).
    * *Input:* "If the other person..." -> *Output:* "**Moses reasoned**, 'If another person...'"

### 2. PHENOMENON OVER LABEL
* **Action:** Describe the effect/meaning, not the technical label.
    * *Input:* "Nimna Hanimnaos" -> *Output:* "**God, who is Infinite, and therefore contains the finite.**"

### 3. THE "QUOTE CONTEXT" RULE
* **Liturgy:** Translate objects of study literally ("**Hear O Israel...**").
* **Prooftext:** Translate the point of the quote ("**Man was born to toil**").

# MODULE D: CULTURAL & LINGUISTIC TRANSLATION
### 4. CONCEPT OVER ETYMOLOGY
* **Action:** Translate the *implication*, not the literal word.
    * *Input:* "Chozer L'buryo" -> "**Returns to full health**" (NOT "Returns to his wholeness").
    * *Input:* "Adam" -> "**Created in God's image.**"

### 5. MECHANICS VS. MEANING
* **Action:** If text uses mechanics (Gematria/Letters) to explain a concept, translate the **concept**.

### 6. RELATIONAL TITLES
* **Action:** *Der Rebbe (Nishmaso Eden)* -> "**My father-in-law, the Rebbe.**"

# MODULE E: VISUAL STRUCTURE & RHYTHM
* **Length:** Max 42 characters per line.
* **Balance:** If using 2 lines, keep them roughly equal in length.
* **Split:** Use the tilde symbol `~` to indicate a visual line break inside a single subtitle row.

# MODULE F: SYNTAX (The "Manual" Rules)
* **Active Voice:** "It is believed by many" -> "**Many believe**"
* **No Double Negatives:** "Not only will they not disturb" -> "**The government will not disturb; / on the contrary, it will help.**"

# FEW-SHOT EXAMPLES (Correct Style)

### Example 1: Removing "The Rebbe Explains" & Segmentation
*Input:*
וואָרום אף על פי וואָס דער שחרור פון דעם אַלטן רבי'ן איז געווען ביום י"ט כסלו, איז דאָך געווען כמה סיבות וואָס דערפאַר האָט זיך פאַרהאַלטן
*Output:*
001 | וואָרום אף על פי וואָס דער שחרור... | And yes, **the Alter Rebbe**~was technically released on the 19th.
002 | איז דאָך געווען כמה סיבות וואָס דערפאַר האָט זיך פאַרהאַלטן | However, due to various reasons,~he was detained.

### Example 2: Idiomatic Translation (No "Wholeness")
*Input:*
נאָר אויך ער דאַרף צוואוואַרטן ביז "חוזר לבוריו" – ער ווערט אינגאַנצן געזונט
*Output:*
010 | נאָר אויך ער דאַרף צוואוואַרטן ביז "חוזר לבוריו" | One waits until he~"returns to full health."
011 | ער ווערט אינגאַנצן געזונט | Only then is the recovery complete.

### Example 3: Voice Attribution (Internal Character)
*Input:*
משה האט געטראכט אז אויב יענער טוט אזוי...
*Output:*
020 | משה האט געטראכט אז אויב יענער טוט אזוי... | **Moses reasoned:**~"If that person acts this way..."

# TECHNICAL OUTPUT FORMAT
Provide the output as a simple list with 3 columns separated by pipes (|).
Do NOT use Markdown Table syntax. Just raw lines.

Format:
ID | Yiddish Snippet | English Subtitle
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
    st.markdown("### Input") 
    yiddish_text = st.text_area("Paste text here...", height=600, key="input_area")

with col2:
    st.markdown("### Output")
    
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

            status_box.info(f"🚀 Processing with V54 Rules (Model: {target_model})...")
            
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
