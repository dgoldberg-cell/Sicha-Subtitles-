import streamlit as st
import google.generativeai as genai

st.title("Model Checker")
api_key = st.text_input("Enter Key", type="password")

if st.button("Check Models"):
    genai.configure(api_key=api_key)
    try:
        st.write("### Available Models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.code(m.name)
    except Exception as e:
        st.error(f"Error: {e}")
