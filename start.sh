#!/bin/bash
cd "$(dirname "$0")"
echo "=== NEXUS DEFENSE v2 ==="
python3 -c "import flask" 2>/dev/null || pip3 install flask
echo "Server: http://localhost:5000"
python3 server.py
