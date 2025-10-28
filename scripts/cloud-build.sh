#!/bin/bash
# Trigger a Cloud Build from local source
# Usage: ./scripts/cloud-build.sh

set -e

GCLOUD_BIN="$HOME/google-cloud-sdk/bin/gcloud"
export CLOUDSDK_PYTHON=/usr/bin/python3
PROJECT_ID="airy-web-476402-f4"

echo "🚀 Submitting build to Google Cloud Build..."
"$GCLOUD_BIN" builds submit \
  --config=cloudbuild.yaml \
  --project="${PROJECT_ID}" \
  .

echo "✅ Build submitted successfully!"
echo "   View your build at: https://console.cloud.google.com/cloud-build/builds?project=${PROJECT_ID}"
