from groq import Groq

api_key = "your-api=key"  # Paste your key here
client = Groq(api_key=api_key)
try:
    models = client.models.list()
    print("Groq API connection successful. Models:", [m.id for m in models.data])
except Exception as e:
    print("Groq API connection failed:", e)
