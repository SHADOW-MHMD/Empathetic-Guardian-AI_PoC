import os
import google.generativeai as genai

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

print("Testing google.generativeai API...")

try:
    genai.configure(api_key=api_key)
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"- {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

# Test basic models
test_models = ["models/gemini-pro", "gemini-pro", "models/gemini-1.5-pro", "gemini-1.5-pro"]
for model_name in test_models:
    try:
        print(f"\nTesting {model_name}...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello")
        print(f"✓ {model_name} works: {response.text[:50]}...")
        break
    except Exception as e:
        print(f"✗ {model_name} failed: {str(e)[:100]}...")