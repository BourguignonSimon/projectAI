#!/bin/bash
echo "🚀 Démarrage de la Table Ronde..."

# Création dossier logs
mkdir -p logs

# Lancement des Agents en background
nohup python3 agent_manager.py > logs/manager.log 2>&1 &
echo $! > logs/manager.pid

nohup python3 agent_generic.py --role analyst > logs/analyst.log 2>&1 &
echo $! > logs/analyst.pid

nohup python3 agent_generic.py --role architect > logs/architect.log 2>&1 &
echo $! > logs/architect.pid

nohup python3 agent_generic.py --role coder > logs/coder.log 2>&1 &
echo $! > logs/coder.pid

nohup python3 agent_generic.py --role reviewer > logs/reviewer.log 2>&1 &
echo $! > logs/reviewer.pid

echo "✅ Agents en ligne. Lancement de l'interface..."
streamlit run app.py
