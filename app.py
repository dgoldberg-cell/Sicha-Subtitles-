import streamlit as st
import google.generativeai as genai
from docx import Document
import io

# --- PAGE SETUP ---
st.set_page_config(page_title="Sicha Translator V23", layout="wide")
st.title("⚡ Sicha Translator (Gemini V23)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    # Get your key from: https://aistudio.google.com/
    api_key = st.text_input("Enter Google API Key", type="password")
    
    # --- THE V23 MASTER PROMPT ---
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
010
The government will not disturb;
011
on the contrary, it will help.

### Example B: Active Voice & Visual Balance
*Input:*
ס'איז דאָך ידוע דער וואָרט פון דעם רבי'ן נשמתן עדן
*Output:*
025
**My father-in-law, the Rebbe,**
taught the following:

### Example C: Mechanics vs. Meaning & Integration
*Input:*
דער חי"ת איז דאָס די ז' רקיעים... זאגט אים תורת אמת אז "היום" איז דאס "לעשותם"
*Output:*
049
Since a child can already
see the sky and earth,
050
the Torah of Truth informs him
that this world was created for "toil."
    """
    
    with st.expander("Edit System Prompt"):
        system_prompt = st.text_area("Prompt", value=default_prompt, height=300)

# --- MAIN PAGE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input (Yiddish)")
    yiddish_text = st.text_area("Paste text here...", height=500)

with col2:
    st.subheader("Output (English)")
    if st.button("Translate"):
        if not api_key:
            st.error("Please put your Google API Key in the sidebar.")
        elif not yiddish_text:
            st.warning("Please paste some Yiddish text.")
        else:
            try:
                genai.configure(api_key=api_key)
                # Use Gemini 1.5 Flash for speed/cost, or 1.5 Pro for quality
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash-latest",
                    system_instruction=system_prompt
                )
                with st.spinner("Translating..."):
                    response = model.generate_content(yiddish_text)
                    st.session_state['result'] = response.text
            except Exception as e:
                st.error(f"Error: {e}")

    if 'result' in st.session_state:
        st.text_area("Result", value=st.session_state['result'], height=500)
        
        # Word Doc Export
        doc = Document()
        doc.add_paragraph(st.session_state['result'])
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button(
            label="Download Word Doc",
            data=bio.getvalue(),
            file_name="translation.docx",
            mime="application/docx"

        )
