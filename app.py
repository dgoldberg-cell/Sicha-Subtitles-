import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V25 (Auto-Pilot)", layout="wide")
st.title("⚡ Sicha Translator (Auto-Pilot)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    
    # 1. API Key
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # 2. Output Settings
    st.divider()
    st.subheader("Output Style")
    output_format = st.radio(
        "Choose Layout:",
        ["Side-by-Side Table (Clean Yiddish | English)", "English Subtitles Only"]
    )
    st.divider()
    
    st.info("ℹ️ System is running in **Auto-Pilot Mode**. It will automatically find the best available model for your key.")

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
    
    with st.expander("Advanced: Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=300)

# --- MODEL PRIORITY LIST (The Auto-Pilot Brain) ---
# The system will try these in order until one works.
MODEL_PRIORITY = [
    "gemini-2.5-flash",          # Newest, Fast
    "gemini-2.0-flash",          # Stable, Fast
    "gemini-1.5-pro",            # High Intelligence
    "gemini-1.5-flash",          # Reliable Fallback
    "gemini-1.5-flash-8b",       # Experimental/Cheaper
    "gemini-1.5-pro-001"         # Specific Version Fallback
]

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=600)

with col2:
    st.subheader("Output")
    if st.button("Translate (Auto-Pilot)", type="primary"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            
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

            # --- THE AUTO-PILOT LOOP ---
            success = False
            status_box = st.empty() # Placeholder for status updates
            
            genai.configure(api_key=api_key)

            for model_name in MODEL_PRIORITY:
                try:
                    status_box.caption(f"🚀 Trying model: **{model_name}**...")
                    
                    # Initialize Model
                    model = genai.GenerativeModel(
                        model_name=model_name, 
                        system_instruction=final_instruction
                    )
                    
                    # Attempt Generation
                    response = model.generate_content(yiddish_text)
                    
                    # If we get here, it worked!
                    st.session_state['result'] = response.text
                    st.session_state['used_model'] = model_name
                    success = True
                    status_box.success(f"✅ Success! Used model: **{model_name}**")
                    break # Stop the loop
                    
                except Exception as e:
                    # If error, print tiny warning and continue loop
                    print(f"Model {model_name} failed: {e}")
                    status_box.warning(f"⚠️ {model_name} failed (404/429). Switching...")
                    time.sleep(0.5) # Brief pause before retry

            if not success:
                st.error("❌ All models failed. Please check your API Key or try again later.")

    if 'result' in st.session_state:
        # RENDER AS MARKDOWN
        st.markdown(st.session_state['result'])
        
        st.divider()
        st.caption(f"Generated using: **{st.session_state.get('used_model', 'Unknown')}**")
        
        # EXPORT TOOLS
        doc = Document()
        doc.add_heading(f"Translation ({st.session_state.get('used_model')})", 0)
        doc.add_paragraph(st.session_state['result'])
        bio = io.BytesIO()
        doc.save(bio)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="Download Word Doc",
                data=bio.getvalue(),
                file_name="translation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        with col_d2:
             st.download_button(
                label="Download Raw Text",
                data=st.session_state['result'],
                file_name="translation.txt",
                mime="text/plain"
            )
