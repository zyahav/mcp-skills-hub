#!/bin/bash
echo "👀 Watching for changes in mcp-skills-hub..."

last_checksum=""

while true; do
    # Calculate checksum of all python files
    current_checksum=$(find . -name "*.py" -not -path "*/__pycache__/*" -exec md5 -q {} + | md5)
    
    if [ "$last_checksum" != "$current_checksum" ]; then
        if [ -n "$last_checksum" ]; then
            echo "🔄 Change detected! Running tests..."
            /opt/homebrew/bin/python3 -m unittest tests/test_skills.py
            echo "---------------------------------------------------"
            echo "👀 Waiting for changes..."
        fi
        last_checksum=$current_checksum
    fi
    sleep 2
done
