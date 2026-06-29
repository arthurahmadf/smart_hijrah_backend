# test_groq_simple.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

try:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # coba model ini
        messages=[
            {"role": "user", "content": "Apa hukum puasa?"}
        ],
        temperature=0.7,
        max_tokens=512
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")