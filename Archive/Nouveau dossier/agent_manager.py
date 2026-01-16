import time
import os
from utils import r, STREAM_KEY, publish_message, get_ai_response

def save_project_to_disk(code_content):
    """Matérialise le code final sur le disque."""
    if not os.path.exists("output"):
        os.makedirs("output")
    with open("output/final_product.py", "w") as f:
        f.write(code_content)
    return "Fichier 'output/final_product.py' sauvegardé avec succès."

def run_manager():
    print("🤖 MANAGER (Scrum Master) est en ligne...")
    last_id = '$' # Lire seulement les nouveaux messages
    rejection_count = 0 # Circuit Breaker

    while True:
        # Lecture bloquante de Redis
        messages = r.xread({STREAM_KEY: last_id}, count=1, block=5000)
        
        if messages:
            stream, msgs = messages[0]
            last_id = msgs[0][0]
            data = msgs[0][1]
            sender = data['sender']
            content = data['content']
            msg_type = data.get('type', 'message')

            # Logique d'Orchestration (State Machine simplifiée)
            if sender == 'user' and msg_type == 'order':
                publish_message('manager', f"Bien reçu. @Analyst, analyse cette demande : {content}", "command")
            
            elif sender == 'analyst' and msg_type == 'report':
                publish_message('manager', "Merci. @Architect, propose une structure technique pour ces specs.", "command")
            
            elif sender == 'architect' and msg_type == 'plan':
                publish_message('manager', "Validé. @Coder, écris le code complet en Python.", "command")

            elif sender == 'coder' and msg_type == 'code':
                publish_message('manager', "Code reçu. @Reviewer, vérifie ce code (Sécurité, Logique).", "command")

            elif sender == 'reviewer':
                if "VALIDATED" in content:
                    publish_message('manager', "Projet validé ! Sauvegarde en cours...", "info")
                    # Extraction du code (simplifié pour la démo)
                    # Dans une version prod, on parserait le JSON ou le bloc Markdown
                    last_code = r.xrevrange(STREAM_KEY, count=10) # Récupérer le dernier code du codeur
                    save_status = save_project_to_disk("print('Code Final Placeholder - Voir logs')") 
                    publish_message('manager', f"TERMINÉ. {save_status}", "finished")
                else:
                    rejection_count += 1
                    if rejection_count >= 3:
                        publish_message('manager', "FATAL ERROR: Trop de rejets. Arrêt d'urgence.", "error")
                    else:
                        publish_message('manager', f"Rejeté ({rejection_count}/3). @Coder, corrige selon les remarques du Reviewer.", "command")

if __name__ == "__main__":
    run_manager()
