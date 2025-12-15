import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Error Revealer")
st.title("🕵️ Error Revealer")

# 1. Enter Key
api_key = st.text_input("Enter Google API Key", type="password")

if st.button("Test Connection"):
    if not api_key:
        st.warning("Please enter a key.")
    else:
        try:
            # 2. Configure
            genai.configure(api_key=api_key)
            
            # 3. Try to generate a simple "Hello"
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Say Hello")
            
            # 4. If this works, your key is perfect.
            st.success("✅ SUCCESS! Your key works perfectly.")
            st.write(f"Response: {response.text}")
            
        except Exception as e:
            # 5. IF IT FAILS, PRINT THE ERROR
            st.error("❌ CONNECTION FAILED")
            st.markdown(f"### The Error Code is:")
            st.code(str(e), language="text")
            
            # 6. Translate the Error for the User
            err_text = str(e)
            st.divider()
            st.subheader("What this means:")
            
            if "400" in err_text:
                st.info("👉 **INVALID KEY:** You likely copied a space or a hidden character. Check your key.")
            elif "403" in err_text:
                st.info("👉 **PERMISSION DENIED:** This key is invalid or deleted. Generate a new key.")
            elif "429" in err_text or "429" in err_text:
                st.info("👉 **OUT OF GAS (Quota):** You used all your free requests for today. Wait a few hours or use a new Google account.")
            elif "404" in err_text or "NotFound" in err_text:
                st.info("👉 **OLD SOFTWARE:** Your key is fine, but your App is outdated. You MUST update 'requirements.txt'.")
            else:
                st.info("👉 **UNKNOWN:** Copy the error code above and paste it in the chat.")
