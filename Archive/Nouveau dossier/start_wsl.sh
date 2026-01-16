#!/bin/bash

# Fonction pour tuer les processus background en quittant
cleanup() {
    echo ""
    echo "🛑 Arrêt des agents..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Piéger le CTRL+C pour tout nettoyer
trap cleanup SIGINT SIGTERM

echo "🚀 Démarrage de l'infrastructure 'La Table Ronde'..."

# Création des logs si inexistant
mkdir -p logs

# Lancement des Agents (Silencieux)
echo "   - Lancement du Manager..."
python3 agent_manager.py > logs/manager.log 2>&1 &

echo "   - Lancement de l'Analyste..."
python3 agent_generic.py --role analyst > logs/analyst.log 2>&1 &

echo "   - Lancement de l'Architecte..."
python3 agent_generic.py --role architect > logs/architect.log 2>&1 &

echo "   - Lancement du Codeur..."
python3 agent_generic.py --role coder > logs/coder.log 2>&1 &

echo "   - Lancement du Reviewer..."
python3 agent_generic.py --role reviewer > logs/reviewer.log 2>&1 &

# Pause pour laisser le temps aux connexions Redis
sleep 2

# Lancement du client interactif (Au premier plan)
python3 client_terminal.py

# Si on quitte le python script, on arrive ici et le trap cleanup se déclenche
cleanup
