import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V36 (Self-Diagnosing)", layout="wide")
st.title("⚡ Sicha Translator (Storyteller V36)")

# --- CRITICAL: SELF-DIAGNOSIS ---
try:
    library_version = genai.__version__
    major, minor, patch = map(int, library_version.split('.'))
    
    # We need at least version 0.8.3 for the new models
    if minor < 8 and major == 0:
        st.error(f"🛑 CRITICAL SYSTEM ERROR")
        st.error(f"Your System Brain is too old: Version {library_version}")
        st.warning("👉 YOU MUST FIX 'requirements.txt' NOW.")
        st.info("1. Go to GitHub.\n2. Open 'requirements.txt'.\n3. Delete everything.\n4. Paste this:\n\nstreamlit\ngoogle-generativeai>=0.8.3\npandas\npython-docx")
        st.stop() # STOP THE APP HERE
        
except Exception as e:
    st.error(f"System Check Failed: {e}")

# --- IF WE PASS THE CHECK, WE LOAD THE APP ---

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    st.divider()
    st.info(f"✅ System Status: Healthy\nBrain Version: {library_version}")

    # --- THE MASTER ENGLISH PROMPT ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: FIDELITY
* Do not summarize. Translate every thought.

# MODULE B: NARRATIVE & THEOLOGY
* **Voice:** "Moses reasoned..."
* **Concepts:** Describe meaning, not labels.
* **Quotes:** Liturgy = Literal. Prooftext = Meaning.

# MODULE C: CULTURAL
* *Adam* -> "Created in God's image."
* *Der Rebbe* -> "My father-in-law, the Rebbe."

# MODULE D: VISUAL STRUCTURE (The "Vertical Flow")
* **CRITICAL:** Output must be a vertical list of subtitles.
* **Length:** Keep lines short (3-7 words).
* **Format:** Use the tilde `~` to split a single subtitle into two lines if needed.

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
        system_prompt = st.text_area("Prompt", value=default_prompt, height=300)

# --- MODEL PRIORITY LIST ---
MODEL_PRIORITY = [
    "gemini-2.0-flash",          
    "gemini-1.5-pro",            
    "gemini-1.5-flash",          
    "gemini-1.5-flash-8b"       
]

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=600, label_visibility="collapsed")

with col2:
    st.subheader("Output")
    
    if st.button("Translate", type="primary"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            
            # --- EXECUTION LOOP ---
            success = False
            status_box = st.empty()
            
            genai.configure(api_key=api_key)

            for model_name in MODEL_PRIORITY:
                try:
                    status_box.info(f"⏳ Trying model: **{model_name}**...")
                    
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                    response = model.generate_content(yiddish_text)
                    
                    st.session_state['result'] = response.text
                    st.session_state['used_model'] = model_name
                    success = True
                    status_box.success(f"✅ Success! Used: {model_name}")
                    break 
                except Exception as e:
                    # PRINT THE EXACT ERROR FOR DEBUGGING
                    st.warning(f"⚠️ {model_name} Failed. Error: {e}")
                    time.sleep(1)

            if not success:
                st.error("❌ CRITICAL FAILURE. Read the yellow warnings above to see why.")

    # --- RESULT PROCESSING ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        
        # Parse data
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
            
            # DISPLAY AS VERTICAL CARDS (Standard Clean UI)
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 4, 4])
                    
                    c1.caption(f"**{row['#']}**")
                    c2.text(row['Yiddish'])
                    c3.markdown(f"#### {row['English']}", unsafe_allow_html=True)
                    
                    st.divider()
            
            # WORD DOC EXPORT
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
                row_cells[2].text = row['English'].replace("<br>", "\n")

            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="Download Word Doc",
                data=bio.getvalue(),
                file_name="translation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.text(raw_text)
