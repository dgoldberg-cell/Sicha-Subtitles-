import google.generativeai as genai
import os

# 1. Paste your API Key here directly to test
api_key = "AIzaSyClr2evZWaHQMo6Ww4lNxgYzNCvM1GDoxI"

genai.configure(api_key=api_key)

print("--- AVAILABLE MODELS ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error: {e}")
