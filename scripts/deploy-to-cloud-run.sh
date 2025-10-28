#!/bin/bash
# Deploy to Google Cloud Run with environment variables
# Usage: ./scripts/deploy-to-cloud-run.sh

set -e

GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"
export CLOUDSDK_PYTHON=/usr/bin/python3
PROJECT_ID="airy-web-476402-f4"
REGION="northamerica-northeast2"
SERVICE_NAME="aether-web"
IMAGE="northamerica-northeast2-docker.pkg.dev/${PROJECT_ID}/aether/aether-app:latest"
ENV_FILE=".env.cloudrun"

echo "🚀 Deploying to Cloud Run..."
echo "   Service: ${SERVICE_NAME}"
echo "   Image: ${IMAGE}"
echo "   Region: ${REGION}"
echo "   Env File: ${ENV_FILE}"
echo ""

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: ${ENV_FILE} not found!"
    echo "Please create ${ENV_FILE} with your environment variables."
    exit 1
fi

# Deploy to Cloud Run
"$GCLOUD_BIN" run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300 \
  --env-vars-file="${ENV_FILE}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URL:"
"$GCLOUD_BIN" run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)"
