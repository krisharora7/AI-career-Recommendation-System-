import os
import requests

# Set your Groq API key here or via environment variable
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# LLaMA-3 model is best supported by Groq
MODEL_NAME = "llama3-70b-8192"

def ask_bot(user_message: str) -> str:
    """
    Sends the user's message to the Groq API and returns the chatbot's reply.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are CareerMind.AI, an expert career assistant built by Krish Arora. Help the user explore career paths based on AI recommendations."},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        return f"❌ HTTP error: {http_err}"
    except requests.exceptions.RequestException as req_err:
        return f"❌ Connection error: {req_err}"
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"
