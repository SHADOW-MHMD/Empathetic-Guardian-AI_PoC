import os
from dotenv import load_dotenv

# Force load .env at the very top
load_dotenv()

from google import genai

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
print(f"API key loaded: {api_key is not None}")
print(f"API key length: {len(api_key) if api_key else 0}")
print(f"API key starts with: {api_key[:15] if api_key else 'None'}...")
print(f"Using API Key: {api_key[:5]}***" if api_key else "No API key found")

if not api_key:
    print("No API key found")
    exit(1)

try:
    print("Creating genai client...")
    client = genai.Client(api_key=api_key)
    print("Client creation successful")

    print("Listing models...")
    models = client.models.list()
    print(f"Found models:")
    for model in models[:5]:  # Show first 5
        print(f"- {model.name}")

    print("\nTesting models/gemini-2.0-flash...")
    test_response = client.models.generate_content(
        model='models/gemini-2.0-flash',
        contents="Hello, this is a test message."
    )
    print("✓ models/gemini-2.0-flash works!")
    print(f"Response: {test_response.text[:100]}...")

except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")