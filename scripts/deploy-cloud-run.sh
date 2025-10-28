#!/bin/bash
# Deploy to Google Cloud Run
# Usage: ./scripts/deploy-cloud-run.sh

set -e

GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"
export CLOUDSDK_PYTHON=/usr/bin/python3
PROJECT_ID="airy-web-476402-f4"
REGION="northamerica-northeast2"
SERVICE_NAME="aether-web"
IMAGE="northamerica-northeast2-docker.pkg.dev/${PROJECT_ID}/aether/aether-app:latest"

echo "🚀 Deploying to Cloud Run..."
echo "   Service: ${SERVICE_NAME}"
echo "   Image: ${IMAGE}"
echo "   Region: ${REGION}"

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
  --set-env-vars="ENVIRONMENT=production"

echo "✅ Deployment complete!"
echo ""
echo "Service URL:"
"$GCLOUD_BIN" run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)"
