import argparse
import time
from utils import r, STREAM_KEY, publish_message, get_ai_response

# Définition des Personnalités
PROMPTS = {
    "analyst": "Tu es un Business Analyst expert. Transforme la demande floue du client en User Stories claires et techniques.",
    "architect": "Tu es un Architecte Logiciel Senior. Décide de la stack (Python, Redis, etc.) et de la structure des fichiers.",
    "coder": "Tu es un Développeur Python Senior. Écris un code PROPRE, documenté et fonctionnel. N'utilise que du code standard.",
    "reviewer": "Tu es un QA Engineer impitoyable. Cherche les bugs, failles de sécurité. Réponds 'VALIDATED' seulement si c'est parfait. Sinon explique pourquoi."
}

def run_agent(role):
    print(f"👤 AGENT {role.upper()} est en ligne...")
    system_prompt = PROMPTS[role]
    last_id = '$'

    while True:
        messages = r.xread({STREAM_KEY: last_id}, count=1, block=5000)
        if messages:
            stream, msgs = messages[0]
            last_id = msgs[0][0]
            data = msgs[0][1]
            sender = data['sender']
            content = data['content']
            
            # L'agent ne réagit que si le Manager le mentionne (ex: "@Analyst")
            if sender == 'manager' and f"@{role.capitalize()}" in content:
                print(f"[{role}] J'ai été appelé ! Travail en cours...")
                
                # Simulation de réflexion/travail (Récupération de l'historique récent)
                history = "Derniers messages du projet..." # Ici on pourrait lire tout le stream
                
                # Appel à l'IA
                response = get_ai_response(role, content, history)
                
                # Le Codeur a une étape spéciale : Test d'exécution (Simulation)
                msg_type = "report"
                if role == "coder":
                    msg_type = "code"
                    try:
                        # Sécurité basique : on vérifie juste la syntaxe
                        compile(response, '<string>', 'exec')
                        response = f"```python\n{response}\n```\n(Compilé avec succès)"
                    except Exception as e:
                        response = f"Erreur de syntaxe détectée : {e}. Je corrige..."
                        # Ici on pourrait relancer une boucle de correction interne

                publish_message(role, response, msg_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=["analyst", "architect", "coder", "reviewer"])
    args = parser.parse_args()
    run_agent(args.role)
