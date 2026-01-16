#!/bin/bash
cleanup() {
    echo ""
    echo "[STOPPING] FACTORY..."
    pkill -f "python3 agent_" || true
    pkill -f "python3 client_" || true
    # Flush main Redis
    if [ "$(docker ps -q -f name=redis-lab)" ]; then
        docker exec redis-lab redis-cli FLUSHALL > /dev/null
    fi
    # Flush routing Redis
    if [ "$(docker ps -q -f name=redis-routing)" ]; then
        docker exec redis-routing redis-cli FLUSHALL > /dev/null
    fi
    echo "[OK] CLEAN EXIT."
}
trap cleanup EXIT SIGINT SIGTERM

echo "[STARTING] SILENT FACTORY..."
mkdir -p logs livrables project_logs

# Start routing Redis on port 6381 if not running
if [ ! "$(docker ps -q -f name=redis-routing)" ]; then
    if [ "$(docker ps -aq -f name=redis-routing)" ]; then
        echo "[INFO] Starting existing redis-routing container..."
        docker start redis-routing > /dev/null
    else
        echo "[INFO] Creating redis-routing container on port 6381..."
        docker run -d --name redis-routing -p 6381:6379 redis:latest > /dev/null
    fi
    sleep 1
fi
echo "[OK] Routing Redis (port 6381) ready"

python3 agent_manager.py > logs/manager.log 2>&1 &
python3 agent_generic.py --role analyst > logs/analyst.log 2>&1 &
python3 agent_generic.py --role architect > logs/architect.log 2>&1 &
python3 agent_generic.py --role coder > logs/coder.log 2>&1 &
python3 agent_generic.py --role reviewer > logs/reviewer.log 2>&1 &

sleep 2
python3 client_terminal.py