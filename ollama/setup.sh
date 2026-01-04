#!/bin/bash
# Setup script for Ollama server

# Start the container
docker compose up -d

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done

# Pull the Qwen model
echo "Pulling qwen2.5 model..."
docker compose exec ollama ollama pull qwen2.5

echo "Done! Ollama is ready at http://$(hostname -I | awk '{print $1}'):11434"
