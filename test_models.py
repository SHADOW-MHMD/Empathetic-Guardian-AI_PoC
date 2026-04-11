import os
from google import genai

# Load API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in environment")
    exit(1)

# Create client - try both methods
print("Testing different API approaches...")

try:
    # Method 1: New Client API
    client = genai.Client(api_key=api_key)
    print("✓ Client API works")
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"- {model.name}")
except Exception as e:
    print(f"Client API failed: {e}")

# Test specific models with Client API
print("\nTesting specific models with Client API:")
test_models = ["gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]
for model_name in test_models:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, test message"
        )
        print(f"✓ {model_name} works")
        if hasattr(response, 'text'):
            print(f"  Response: {response.text[:50]}...")
        break
    except Exception as e:
        print(f"✗ {model_name} failed: {str(e)[:100]}...")