import os
import google.generativeai as genai

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

print("Testing Gemini API...")

try:
    genai.configure(api_key=api_key)
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"- {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error: {e}")

# Test basic model
try:
    print("\nTesting models/gemini-pro...")
    model = genai.GenerativeModel('models/gemini-pro')
    response = model.generate_content("Say hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"models/gemini-pro failed: {e}")

try:
    print("\nTesting gemini-pro...")
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"gemini-pro failed: {e}")