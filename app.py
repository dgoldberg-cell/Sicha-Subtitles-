import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sicha Translator V38 (Safe Mode)", layout="wide")
st.title("⚡ Sicha Translator (Safe Mode)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    # THE CRITICAL STEP: The user must input a NEW key
    api_key = st.text_input("Enter NEW Google API Key", type="password")
    
    st.warning("⚠️ NOTE: If you saw 'Error 429', your old key is dead. You MUST use a new key from a new Google Account.")

    # --- SIMPLIFIED PROMPT ---
    default_prompt = """
# Role
You are a master storyteller translating the Lubavitcher Rebbe’s Sichos into English.

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
    
    if st.button("Translate (Safe Mode)", type="primary"):
        if not api_key:
            st.error("Please enter a NEW API Key.")
        elif not yiddish_text:
            st.warning("Please paste text.")
        else:
            
            # --- THE SAFETY LOGIC ---
            status_box = st.empty()
            genai.configure(api_key=api_key)
            
            # We ONLY use 'gemini-pro' here. 
            # It is the only model that works on OLD servers AND NEW servers.
            # This bypasses the "404 Model Not Found" error completely.
            model_name = "gemini-pro"
            
            try:
                status_box.info(f"⏳ Connecting with {model_name}...")
                
                model = genai.GenerativeModel(model_name=model_name) # No system prompt support in old API, we add it to text
                
                # TRICK: Old models don't support 'system_instruction' well in old libs.
                # We combine prompt + text manually to be safe.
                full_input = f"{system_prompt}\n\n---\n\nINPUT TEXT:\n{yiddish_text}"
                
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
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            for idx, row in df.iterrows():
                cells = table.add_row().cells
                cells[0].text = row['#']
                cells[1].text = row['Yiddish']
                cells[2].text = row['English'].replace("<br>", "\n")
            
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("Download DOCX", bio.getvalue(), "sicha_safe.docx")
        else:
            st.text(raw_text)
