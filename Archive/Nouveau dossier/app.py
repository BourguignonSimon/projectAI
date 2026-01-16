import streamlit as st
import time
from utils import r, STREAM_KEY, publish_message

st.set_page_config(page_title="La Table Ronde AI", layout="wide")

st.title("🏭 Usine Logicielle Autonome")
st.markdown("### Manager: Gemini Pro | Codeurs: Gemini Flash")

# Zone de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] != "user" else "👤"):
            st.markdown(msg["content"])

# Zone de Saisie
user_input = st.chat_input("Décrivez votre projet (ex: Je veux un script de budget personnel)...")

if user_input:
    # 1. Afficher côté utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # 2. Envoyer dans Redis pour le Manager
    publish_message("user", user_input, "order")

# Boucle de lecture temps réel (Polling Redis)
# Note: Streamlit relance le script à chaque interaction, 
# pour le temps réel pur, on utilise une boucle courte ou st.empty
if st.button("Rafraîchir les Logs"):
    # Récupérer les 10 derniers messages du Stream
    raw_msgs = r.xrevrange(STREAM_KEY, count=10)
    # On inverse pour avoir l'ordre chronologique
    for msg_id, data in reversed(raw_msgs):
        sender = data['sender']
        content = data['content']
        # On filtre pour ne pas réafficher ce qu'on a déjà (simplifié)
        st.session_state.messages.append({"role": sender, "content": content})
    st.rerun()

# Zone de téléchargement
if os.path.exists("output/final_product.py"):
    with open("output/final_product.py", "rb") as file:
        st.download_button("📥 Télécharger le Projet", file, file_name="budget_app.py")
