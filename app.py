import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V39 (Full Storyteller)", layout="wide")
st.title("⚡ Sicha Translator (Storyteller Mode)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    # THE CRITICAL STEP: The user must input a NEW key
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    
    st.info("ℹ️ System: English Storyteller Mode")

    # --- THE FULL V33 MASTER PROMPT ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: FIDELITY (The "Zero-Loss" Rule)
* **CRITICAL:** Do not summarize. Every distinct thought in the Yiddish must have a corresponding English phrase.
* **Action:** Change structure for flow, but never remove content.

# MODULE B: NARRATIVE VOICE & THEOLOGY
* **Voice Attribution:** Insert tags to describe internal thought processes.
    * *Input:* "If the other person..." -> *Output:* "**Moses reasoned**, 'If another person...'"
* **Phenomenon Over Label:** Describe the effect/meaning, not the technical label.
    * *Input:* "Nimna Hanimnaos" -> *Output:* "**God, who is Infinite, and therefore contains the finite.**"
* **The "Quote Context" Rule:**
    * **Liturgy:** Translate objects of study literally ("**Hear O Israel...**").
    * **Prooftext:** Translate the point of the quote ("**Man was born to toil**").

# MODULE C: CULTURAL & LINGUISTIC TRANSLATION
* **Concept Over Etymology:** Translate the *implication*. *Adam* -> "**Created in God's image.**"
* **Relational Titles:** *Der Rebbe (Nishmaso Eden)* -> "**My father-in-law, the Rebbe.**"

# MODULE D: VISUAL STRUCTURE & RHYTHM
* **Logic:** Subtitles must be readable in seconds.
* **Action:**
    * **Length:** Max 40 characters (approx 3-7 words) per line.
    * **Balance:** If using 2 lines, keep them roughly equal in length.
    * **Split:** Use the tilde symbol `~` to indicate a visual line break inside a single subtitle row.

# MODULE E: SYNTAX & BREVITY
* **Active Voice:** Convert passive to active. (*"It is believed..."* -> *"**Many believe...**"*)
* **Positive Phrasing:** Avoid double negatives. (*"Not only will they not disturb"* -> *"**The government will help.**"*)

# OUTPUT FORMAT RULE (Strict Pipe-List)
Provide the output as a simple list with 3 columns separated by pipes (|).
Do NOT use Markdown Table syntax (no dashes ---). Just raw lines.

Format:
ID | Yiddish Cleaned | English Subtitle

Example:
001 | (Yiddish Text) | English line one~English line two
002 | (Yiddish Text) | Next English line
    """
    
    with st.expander("Advanced: Edit System Prompt"):
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
            st.error("Please enter a NEW API Key.")
        elif not yiddish_text:
            st.warning("Please paste text.")
        else:
            
            # --- THE SAFETY LOGIC ---
            status_box = st.empty()
            genai.configure(api_key=api_key)
            
            # We use 'gemini-pro' (Legacy) to ensure connection on all servers
            model_name = "gemini-pro"
            
            try:
                status_box.info(f"⏳ Connecting with {model_name}...")
                
                model = genai.GenerativeModel(model_name=model_name)
                
                # TRICK: We manually attach the FULL BRAIN to the user's text
                # This guarantees the model follows instructions even on old software.
                full_input = f"{system_prompt}\n\n---\n\nTASK: Translate the following Yiddish transcript according to the rules above:\n\n{yiddish_text}"
                
                response = model.generate_content(full_input)
                
                st.session_state['result'] = response.text
                status_box.success("✅ Success!")
                
            except Exception as e:
                status_box.error("❌ Failed.")
                err_msg = str(e)
                if "429" in err_msg:
                    st.error("👉 **Error 429: Quota Exceeded.**\nYour API Key is empty. You need a key from a DIFFERENT Google Account.")
                elif "400" in err_msg:
                    st.error("👉 **Error 400: Bad Request.**\nCheck your API Key for spaces/typos.")
                else:
                    st.error(f"Error details: {e}")

    # --- RESULT DISPLAY ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        
        # Simple Parser
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
            
            # Download
            doc = Document()
            doc.add_heading("Sicha Translation", 0)
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '#'
            hdr_cells[1].text = 'Yiddish'
            hdr_cells[2].text = 'English'

            for idx, row in df.iterrows():
                cells = table.add_row().cells
                cells[0].text = row['#']
                cells[1].text = row['Yiddish']
                cells[2].text = row['English'].replace("<br>", "\n")
            
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("Download DOCX", bio.getvalue(), "sicha_translation.docx")
        else:
            st.text(raw_text)
