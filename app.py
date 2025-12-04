import streamlit as st
import google.generativeai as genai
from docx import Document
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V24", layout="wide")
st.title("⚡ Sicha Translator (Clean & Aligned V24)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    
    # 1. API Key
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # 2. Model Selection (With your working model as default)
    model_choice = st.text_input("Model Name", value="gemini-1.5-pro")
    st.caption("Try: gemini-1.5-flash, gemini-2.5-flash, gemini-1.5-pro")

    # 3. OUTPUT FORMAT SELECTOR
    st.divider()
    st.subheader("Output Style")
    output_format = st.radio(
        "Choose Layout:",
        ["Side-by-Side Table (Clean Yiddish | English)", "English Subtitles Only"]
    )
    st.divider()

    # --- THE V24 MASTER PROMPT (CLEAN & ALIGN) ---
    default_prompt = """
# Role
You are a master storyteller and subtitler adapting the Lubavitcher Rebbe’s Sichos.

# MODULE A: THE "JANITOR" (Source Cleaning)
* **CRITICAL:** When outputting the Yiddish Source column, you must CLEAN the text.
* **Remove:** Random symbols (??, *, #), OCR artifacts, and parenthetical interruptions that are not part of the sentence flow.
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
* **Balance:** Two lines should be visually equal (pyramid/rectangle).

### 7. LOGICAL BRIDGING
* **Action:** Insert connectors: **"But first," "However."**

# MODULE F: SYNTAX (The Manual)
### 8. ACTIVE VOICE & POSITIVE PHRASING
* Convert Passive -> Active.
* Convert Double Negative -> Positive + Contrast.

### 9. INTRO REMOVAL
* Remove conversational filler ("I would like to know...").
    """
    
    with st.expander("Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=300)

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=600)

with col2:
    st.subheader("Output")
    if st.button("Translate"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # --- DYNAMIC PROMPT LOGIC ---
                final_instruction = system_prompt
                
                if output_format == "Side-by-Side Table (Clean Yiddish | English)":
                    final_instruction += """
                    \n\nCRITICAL OUTPUT FORMATTING RULE:
                    You must output a CLEAN Markdown Table.
                    | Yiddish Source (Cleaned) | English Subtitle |
                    | :--- | :--- |
                    | (Yiddish text here) | (English text here) |
                    
                    Ensure the Yiddish is right-aligned in logic but displayed clearly.
                    Remove all brackets [] and artifacts from the Yiddish column.
                    """
                else:
                    final_instruction += "\n\nOUTPUT RULE: Provide ONLY the English subtitles in numbered segments (001, 002...)."

                # Initialize Model
                model = genai.GenerativeModel(
                    model_name=model_choice, 
                    system_instruction=final_instruction
                )
                
                with st.spinner("Translating & Cleaning..."):
                    response = model.generate_content(yiddish_text)
                    st.session_state['result'] = response.text

            except Exception as e:
                st.error(f"Error: {e}")

    if 'result' in st.session_state:
        # RENDER AS MARKDOWN (This makes the table look nice)
        st.markdown(st.session_state['result'])
        
        st.divider()
        st.caption("Raw Text for Export:")
        st.text_area("", value=st.session_state['result'], height=200)
        
        # Word Doc Export
        doc = Document()
        doc.add_paragraph(st.session_state['result'])
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button(
            label="Download Word Doc",
            data=bio.getvalue(),
            file_name="translation.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
