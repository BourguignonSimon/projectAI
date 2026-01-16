import os
import redis
import google.generativeai as genai
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

load_dotenv()

# Environment variable validation
REQUIRED_ENV_VARS = ['REDIS_HOST', 'REDIS_PORT', 'GOOGLE_API_KEY', 'MODEL_SMART', 'MODEL_FAST']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

r = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), decode_responses=True)
STREAM_KEY = "table_ronde_stream"

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_next_sequence(request_id):
    if not request_id: return 0
    return r.incr(f"project:{request_id}:sequence")

def log_to_disk(request_id, sequence_id, sender, content, msg_type, status):
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
    """Publie sur Redis avec nettoyage UTF-8 pour éviter les crashs Windows."""
    seq_id = get_next_sequence(request_id)
    
    # Nettoyage des caractères invalides (Surrogates)
    if isinstance(content, str):
        content = content.encode('utf-8', 'replace').decode('utf-8')

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

def compress_history(current_summary, new_messages_text):
    """Compression optimisée 'Token Saver' : Faits techniques uniquement."""
    model = genai.GenerativeModel(os.getenv('MODEL_FAST'))
    prompt = f"""
    TASK: Compress logs into a dense technical state.
    CONSTRAINTS: Bullet points only. No conversational text. Keep filenames, tech stack, and status.
    
    OLD_STATE: {current_summary}
    NEW_EVENTS: {new_messages_text}
    """
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        print(f"Compression error: {e}")
        return current_summary

def build_smart_context(request_id):
    """Mémoire glissante avec compression automatique."""
    if not request_id: return "No context."
    summary_key = f"project:{request_id}:summary"
    last_read_key = f"project:{request_id}:last_read_id"
    
    stored_summary = r.get(summary_key) or "Start."
    last_read_id = r.get(last_read_key) or "0-0"

    new_stream = r.xread({STREAM_KEY: last_read_id}, count=100) 
    new_msgs = []
    
    if new_stream:
        for msg in new_stream[0][1]:
            data = msg[1]
            if data.get('request_id') == request_id:
                new_msgs.append(f"[{data['sender'].upper()}]: {data['content']}")

    if len(new_msgs) > 8: # Seuil de compression
        to_compress = new_msgs[:-4]
        to_keep = new_msgs[-4:]
        new_summary = compress_history(stored_summary, "\n".join(to_compress))
        r.set(summary_key, new_summary)
        
        return f"=== STATE ===\n{new_summary}\n=== RECENT ===\n" + "\n".join(to_keep)
    else:
        return f"=== STATE ===\n{stored_summary}\n=== RECENT ===\n" + "\n".join(new_msgs)

def get_ai_response(role, prompt, full_context=""):
    model_name = os.getenv('MODEL_SMART') if role in ['manager', 'analyst', 'architect'] else os.getenv('MODEL_FAST')
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(f"{full_context}\n\nTASK FOR {role.upper()}: {prompt}")
        return response.text
    except Exception as e:
        return f"AI ERROR: {e}"