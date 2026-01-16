import os
import redis
import google.generativeai as genai
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

load_dotenv()

# Connexion Redis
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), decode_responses=True)
STREAM_KEY = "table_ronde_stream"

# Configuration Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_next_sequence(request_id):
    """Gère le compteur incrémental pour un projet donné via Redis."""
    if not request_id: return 0
    return r.incr(f"project:{request_id}:sequence")

def log_to_disk(request_id, sequence_id, sender, content, msg_type, status):
    """Archive chaque message dans un fichier JSONL dédié au GUID."""
    if not request_id: return

    log_dir = "project_logs"
    if not os.path.exists(log_dir): os.makedirs(log_dir)
    
    filename = f"{log_dir}/project_{request_id}.jsonl"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "sequence": sequence_id,
        "sender": sender,
        "type": msg_type,
        "status": status,
        "content": content
    }
    
    with open(filename, "a", encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def publish_message(sender, content, msg_type="message", request_id=None, status="DONE"):
    """
    Publie dans Redis et archive sur disque.
    status='DONE' indique aux autres agents qu'ils peuvent prendre la main.
    """
    seq_id = get_next_sequence(request_id)
    
    message = {
        "request_id": request_id if request_id else "",
        "sequence_id": seq_id,
        "sender": sender,
        "content": content,
        "type": msg_type,
        "status": status
    }
    
    r.xadd(STREAM_KEY, message)
    log_to_disk(request_id, seq_id, sender, content, msg_type, status)

def get_ai_response(role, prompt, history_context=""):
    """Wrapper pour Gemini : Sélectionne le bon modèle et envoie la requête."""
    # Modèle "Intelligent" pour la conception, "Rapide" pour le code/review (ajustable selon .env)
    model_name = os.getenv('MODEL_SMART') if role in ['manager', 'analyst', 'architect'] else os.getenv('MODEL_FAST')
    
    try:
        model = genai.GenerativeModel(model_name)
        system_instruction = f"Tu es {role}. Contexte du projet : {history_context}"
        # On force la tâche explicite
        full_prompt = f"{system_instruction}\n\nTâche : {prompt}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"[ERREUR IA CRITIQUE] : {str(e)}"