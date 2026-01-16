import time
import sys
import os
from utils import r, STREAM_KEY, publish_message

# Codes couleurs ANSI pour le terminal
COLORS = {
    "manager": "\033[94m",   # Bleu
    "analyst": "\033[96m",   # Cyan
    "architect": "\033[95m", # Magenta
    "coder": "\033[92m",     # Vert
    "reviewer": "\033[93m",  # Jaune
    "user": "\033[97m",      # Blanc
    "RESET": "\033[0m"
}

def type_writer(text, delay=0.005):
    """Effet machine à écrire pour le style"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def listen_to_stream(last_id='$'):
    """Écoute le stream Redis et affiche les logs"""
    print(f"\n{COLORS['manager']}--- ÉCOUTE DU FLUX (CTRL+C pour quitter) ---{COLORS['RESET']}\n")
    try:
        while True:
            # Lecture bloquante (timeout 1s pour permettre l'interruption)
            messages = r.xread({STREAM_KEY: last_id}, count=1, block=1000)
            
            if messages:
                stream, msgs = messages[0]
                last_id = msgs[0][0]
                data = msgs[0][1]
                
                sender = data['sender']
                content = data['content']
                
                # Ne pas réafficher nos propres messages
                if sender == 'user':
                    continue

                color = COLORS.get(sender, COLORS['user'])
                prefix = f"[{sender.upper()}]"
                
                print(f"{color}{prefix.ljust(12)} : ", end="")
                # Si c'est du code, on l'affiche directement, sinon effet machine à écrire
                if "```" in content:
                    print(f"\n{content}\n")
                else:
                    type_writer(content)
                    
                if "TERMINÉ" in content or "FATAL ERROR" in content:
                    print(f"\n{COLORS['manager']}--- FIN DE SÉQUENCE ---{COLORS['RESET']}")
                    break
                    
    except KeyboardInterrupt:
        print("\nArrêt de l'écoute.")

def main():
    os.system('clear')
    print(f"{COLORS['manager']}╔════════════════════════════════════════╗")
    print(f"║   USINE LOGICIELLE IA - TERMINAL MODE  ║")
    print(f"╚════════════════════════════════════════╝{COLORS['RESET']}")
    
    while True:
        try:
            print(f"\n{COLORS['user']}Que voulez-vous construire ? (ou 'q' pour quitter){COLORS['RESET']}")
            user_input = input(">> ")
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                break
            
            if not user_input.strip():
                continue

            # 1. Envoyer la commande
            publish_message("user", user_input, "order")
            print(f"{COLORS['user']}Commande envoyée au Manager...{COLORS['RESET']}")

            # 2. Passer en mode écoute
            # On récupère le dernier ID pour ne lire que les nouvelles réponses
            # Note: dans un vrai scénario de prod, on gérerait mieux l'ID
            listen_to_stream(last_id='$')
            
        except KeyboardInterrupt:
            print("\nAu revoir.")
            break

if __name__ == "__main__":
    main()
