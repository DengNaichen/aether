#!/bin/bash
# Build and push Docker images to Google Artifact Registry
# Usage: ./scripts/build-and-push.sh [tag]

set -e

# Configuration
GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"
export CLOUDSDK_PYTHON=/usr/bin/python3
PROJECT_ID="airy-web-476402-f4"
REGION="northamerica-northeast2"
REPOSITORY="aether"
IMAGE_NAME="aether-app"
IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}"

# Get tag from argument or use git commit SHA
TAG="${1:-$(git rev-parse --short HEAD)}"

echo "🔨 Building Docker image for linux/amd64..."
docker buildx build \
  --platform linux/amd64 \
  -t "${IMAGE_BASE}:${TAG}" \
  -t "${IMAGE_BASE}:latest" \
  .

echo "🔐 Authenticating with Google Cloud..."
"$GCLOUD_BIN" auth print-access-token | docker login -u oauth2accesstoken --password-stdin "${REGION}-docker.pkg.dev"

echo "📤 Pushing image with tag: ${TAG}"
docker push "${IMAGE_BASE}:${TAG}"

echo "📤 Pushing image with tag: latest"
docker push "${IMAGE_BASE}:latest"

echo "✅ Successfully pushed images:"
echo "   ${IMAGE_BASE}:${TAG}"
echo "   ${IMAGE_BASE}:latest"
