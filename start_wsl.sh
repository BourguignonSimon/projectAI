#!/bin/bash
cleanup() {
    echo ""
    echo "🛑 STOPPING FACTORY..."
    pkill -f "python3 agent_" || true
    pkill -f "python3 client_" || true
    if [ "$(docker ps -q -f name=redis-lab)" ]; then
        docker exec redis-lab redis-cli FLUSHALL > /dev/null
    fi
    echo "✅ CLEAN EXIT."
}
trap cleanup EXIT SIGINT SIGTERM

echo "🚀 STARTING SILENT FACTORY..."
mkdir -p logs livrables project_logs

python3 agent_manager.py > logs/manager.log 2>&1 &
python3 agent_generic.py --role analyst > logs/analyst.log 2>&1 &
python3 agent_generic.py --role architect > logs/architect.log 2>&1 &
python3 agent_generic.py --role coder > logs/coder.log 2>&1 &
python3 agent_generic.py --role reviewer > logs/reviewer.log 2>&1 &

sleep 2
python3 client_terminal.py