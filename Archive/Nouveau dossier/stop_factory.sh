#!/bin/bash
echo "🛑 Arrêt de l'usine..."
kill $(cat logs/manager.pid)
kill $(cat logs/analyst.pid)
kill $(cat logs/architect.pid)
kill $(cat logs/coder.pid)
kill $(cat logs/reviewer.pid)
echo "L'usine est fermée."
