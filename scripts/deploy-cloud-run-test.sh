#!/bin/bash
# Quick test deployment to Cloud Run (without databases)
# Just to verify the image and port configuration work

set -e

GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"
export CLOUDSDK_PYTHON=/usr/bin/python3
PROJECT_ID="airy-web-476402-f4"
REGION="northamerica-northeast2"
SERVICE_NAME="aether-web-test"
IMAGE="northamerica-northeast2-docker.pkg.dev/${PROJECT_ID}/aether/aether-app:latest"

echo "🧪 Test deployment to Cloud Run (without databases)..."
echo "   Service: ${SERVICE_NAME}"
echo "   Image: ${IMAGE}"

# Deploy with minimal configuration
"$GCLOUD_BIN" run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1 \
  --timeout=60 \
  --set-env-vars="ENVIRONMENT=test,DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test,NEO4J_URI=neo4j://localhost:7687,NEO4J_USER=neo4j,NEO4J_PASSWORD=test,REDIS_URL=redis://localhost:6379/0,SECRET_KEY=test-key-for-cloud-run-deployment-only,ALGORITHM=HS256"

echo "✅ Test deployment complete!"
echo ""
echo "Test the /health endpoint:"
SERVICE_URL=$("$GCLOUD_BIN" run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo "${SERVICE_URL}/health"
echo ""
echo "Note: Database connections will fail, but the service should start and respond on the correct port."
