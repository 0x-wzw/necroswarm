#!/bin/bash
# deploy.sh — Server-side deployment script invoked by the deployment agent via SSH.
# Usage: ./deploy.sh <IMAGE_TAG>

set -euo pipefail

IMAGE_TAG=${1:?Usage: deploy.sh <IMAGE_TAG>}
HEALTH_PORT=${HEALTH_PORT:-3000}
HEALTH_PATH=${HEALTH_PATH:-/api/health}

echo "[deploy] Starting deployment of image: $IMAGE_TAG"

echo "[deploy] Pulling latest image..."
docker compose pull

echo "[deploy] Stopping existing containers..."
docker compose down --timeout 30

echo "[deploy] Starting new containers..."
IMAGE_TAG="$IMAGE_TAG" docker compose up -d

echo "[deploy] Waiting for service to become healthy..."
sleep 5

HEALTH_URL="http://localhost:${HEALTH_PORT}${HEALTH_PATH}"
echo "[deploy] Checking health at ${HEALTH_URL}..."
if ! curl -sf "${HEALTH_URL}" > /dev/null; then
  echo "[deploy] Health check FAILED. Rolling back..."
  docker compose down --timeout 10
  exit 1
fi

echo "[deploy] Deployment COMPLETE: $IMAGE_TAG"
