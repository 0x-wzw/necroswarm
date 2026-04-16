#!/bin/bash
# moltbook.sh — Moltbook CLI client
# Usage: ./moltbook.sh <command> [args]

CREDENTIALS="${HOME}/.config/moltbook/credentials.json"
API_BASE="${MOLTBOOK_API_BASE:-https://api.moltbook.ai}"

get_credentials() {
  if [ ! -f "$CREDENTIALS" ]; then
    echo "Error: Credentials not found at $CREDENTIALS"
    echo "Create it with: mkdir -p ~/.config/moltbook && cat > $CREDENTIALS << 'EOF'
{
  \"api_key\": \"your_key_here\",
  \"agent_name\": \"YourAgentName\"
}
EOF"
    exit 1
  fi
  API_KEY=$(jq -r '.api_key' "$CREDENTIALS")
  AGENT_NAME=$(jq -r '.agent_name' "$CREDENTIALS")
}

api_get() {
  local endpoint="$1"
  curl -s -H "Authorization: Bearer ${API_KEY}" \
       -H "X-Agent-Name: ${AGENT_NAME}" \
       "${API_BASE}${endpoint}"
}

api_post() {
  local endpoint="$1"
  local data="$2"
  curl -s -X POST -H "Authorization: Bearer ${API_KEY}" \
       -H "Content-Type: application/json" \
       -H "X-Agent-Name: ${AGENT_NAME}" \
       -d "$data" \
       "${API_BASE}${endpoint}"
}

cmd_hot() {
  local limit="${1:-5}"
  api_get "/posts?sort=hot&limit=${limit}" | jq .
}

cmd_new() {
  local limit="${1:-5}"
  api_get "/posts?sort=new&limit=${limit}" | jq .
}

cmd_reply() {
  local post_id="$1"
  local content="$2"
  if [ -z "$post_id" ] || [ -z "$content" ]; then
    echo "Usage: moltbook.sh reply <post_id> <content>"
    exit 1
  fi
  api_post "/posts/${post_id}/comments" "{\"content\":\"${content}\"}" | jq .
}

cmd_create() {
  local title="$1"
  local content="$2"
  if [ -z "$title" ] || [ -z "$content" ]; then
    echo "Usage: moltbook.sh create <title> <content>"
    exit 1
  fi
  api_post "/posts" "{\"title\":\"${title}\",\"content\":\"${content}\"}" | jq .
}

cmd_test() {
  api_get "/posts?limit=1" | jq . > /dev/null 2>&1 && echo "✓ Connection OK" || echo "✗ Connection failed"
}

case "$1" in
  hot|new|reply|create|test) get_credentials; cmd_$1 "${@:2}" ;;
  *) echo "Usage: moltbook.sh <hot|new|reply|create|test> [args]"
     echo "  hot [N]      — show N hot posts (default 5)"
     echo "  new [N]      — show N new posts (default 5)"
     echo "  reply ID TXT — reply to post ID"
     echo "  create T C   — create post with title T and content C"
     echo "  test         — test API connection"
     ;;
esac
