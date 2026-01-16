#!/bin/bash
echo "💣 FACTORY RESET..."
pkill -f "python3 agent_" || true
pkill -f "python3 client_" || true
rm -f logs/*.log 2>/dev/null
rm -f project_logs/*.jsonl 2>/dev/null
rm -f livrables/*.py 2>/dev/null
if [ "$(docker ps -q -f name=redis-lab)" ]; then
    docker exec redis-lab redis-cli FLUSHALL > /dev/null
fi
echo "✨ SYSTEM CLEAN."