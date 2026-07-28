#!/usr/bin/env bash
set -euo pipefail

echo "==> Local LLM Benchmark (Ollama)"
echo ""

MODEL="llama3.1:8b-instruct-q4_K_M"
ENDPOINT="http://localhost:11434/v1"

# 1. Check Ollama is running
if ! curl -s "$ENDPOINT/../.." > /dev/null 2>&1; then
  echo "ERROR: Ollama is not running at $ENDPOINT"
  exit 1
fi

echo "Ollama endpoint: $ENDPOINT"
echo "Model: $MODEL"
echo ""

# 2. Simple chat completion benchmark
echo "--- Chat completion ---"
time curl -s "$ENDPOINT/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Say hello in exactly 5 words.\"}],
    \"max_tokens\": 50
  }" | jq '.choices[0].message.content // .error' 2>/dev/null || echo "(jq not installed, raw output above)"

echo ""

# 3. Embedding benchmark
echo "--- Embedding ---"
time curl -s "$ENDPOINT/embeddings" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"input\": \"This is a sample text for embedding.\"
  }" | jq '.data[0].embedding | length' 2>/dev/null || echo "(jq not installed)"

echo ""
echo "==> Benchmark complete"
