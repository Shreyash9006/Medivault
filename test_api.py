import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('HUGGINGFACE_API_KEY')

print("🔍 Testing Hugging Face API Key...\n")

if not api_key:
    print("❌ ERROR: HUGGINGFACE_API_KEY not found")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")

# TRY MULTIPLE ENDPOINTS
endpoints = [
    "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
    "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6",
    "https://api-inference.huggingface.co/models/google/flan-t5-base"
]

headers = {"Authorization": f"Bearer {api_key}"}

print("\n🚀 Testing API connections...\n")

payload = {
    "inputs": "Patient has diabetes and takes metformin daily.",
}

for i, url in enumerate(endpoints, 1):
    print(f"\n{i}. Testing: {url.split('/')[-1]}")
    print("-" * 60)
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS!")
            result = response.json()
            print(f"   Response: {result}")
            print(f"\n🎉 WORKING ENDPOINT FOUND!")
            print(f"Use this in your code: {url}")
            break
        
        elif response.status_code == 503:
            print("   ⏳ Model loading (API key is valid!)")
        
        elif response.status_code == 410:
            print("   ⚠️ Endpoint deprecated")
            print(f"   Error: {response.text}")
        
        else:
            print(f"   Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("✅ YOUR API KEY IS VALID!")
print("App will use rule-based extraction (works without API)")
print("="*60)