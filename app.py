import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V30 (Vertical Flow)", layout="wide")
st.title("⚡ Sicha Translator (Vertical Flow V30)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Google API Key", type="password")
    st.divider()
    st.info("ℹ️ **Auto-Pilot Active:** System will find the best model for your key.")

    # --- THE V30 MASTER PROMPT (VERTICAL LIST) ---
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
    
    if st.button("Translate", type="primary"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            
            # --- AUTO-PILOT LOOP ---
            success = False
            genai.configure(api_key=api_key)

            for model_name in MODEL_PRIORITY:
                try:
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                    response = model.generate_content(yiddish_text)
                    st.session_state['result'] = response.text
                    st.session_state['used_model'] = model_name
                    success = True
                    break 
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    time.sleep(0.5)

            if not success:
                st.error("❌ All models failed.")

    # --- RESULT PROCESSING ---
    if 'result' in st.session_state:
        raw_text = st.session_state['result']
        
        # Parse data
        data = []
        for line in raw_text.split('\n'):
            if "|" in line and "ID |" not in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    data.append({
                        "#": parts[0].strip(), 
                        "Yiddish": parts[1].strip(), 
                        "English": parts[2].strip().replace("~", "<br>")
                    })
        
        if data:
            df = pd.DataFrame(data)
            
            # DISPLAY AS VERTICAL CARDS (Not a crammed table)
            for index, row in df.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 4, 4])
                    c1.caption(row['#'])
                    c2.text(row['Yiddish'])  # Raw text for Yiddish
                    c3.markdown(f"**{row['English']}**", unsafe_allow_html=True) # Bold + Breaks for English
                    st.divider()
            
            # WORD DOC EXPORT (Table Format)
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
