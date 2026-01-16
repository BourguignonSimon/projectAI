import os
import redis
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

# Connexion Redis
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), decode_responses=True)
STREAM_KEY = "table_ronde_stream"

# Configuration Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_ai_response(role, prompt, context_history):
    """Interroge Gemini avec le bon modèle selon le rôle."""
    model_name = os.getenv('MODEL_SMART') if role in ['manager', 'analyst', 'architect'] else os.getenv('MODEL_FAST')
    model = genai.GenerativeModel(model_name)
    
    # Construction du prompt système
    full_prompt = f"Role: {role}.\nContext: {context_history}\nTask: {prompt}"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"ERROR: {str(e)}"

def publish_message(sender, content, type="message"):
    """Publie un message dans le Stream Redis."""
    message = {"sender": sender, "content": content, "type": type}
    r.xadd(STREAM_KEY, message)
    print(f"[{sender}] {content[:50]}...") # Log console
