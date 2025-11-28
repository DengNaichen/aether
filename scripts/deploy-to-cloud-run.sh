#!/bin/bash

# Aether - Deploy to Google Cloud Run with Cloud SQL
# This script deploys the application to Google Cloud Run and sets up Cloud SQL

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - Update these values
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="aether-api"
SQL_INSTANCE_NAME="aether-db-instance"
DATABASE_NAME="aether_db"
DATABASE_USER="aether_user"

# Image configuration
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${GREEN}=== Aether Cloud Run Deployment ===${NC}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}Please authenticate with Google Cloud:${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

echo -e "${YELLOW}Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_NAME}:latest

# Check if Cloud SQL instance exists
echo -e "${YELLOW}Checking Cloud SQL instance...${NC}"
if gcloud sql instances describe ${SQL_INSTANCE_NAME} --format="value(name)" 2>/dev/null; then
    echo -e "${GREEN}Cloud SQL instance ${SQL_INSTANCE_NAME} already exists${NC}"
else
    echo -e "${YELLOW}Creating Cloud SQL instance (this may take several minutes)...${NC}"
    gcloud sql instances create ${SQL_INSTANCE_NAME} \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=${REGION} \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=4 \
        --no-assign-ip

    echo -e "${GREEN}Cloud SQL instance created${NC}"
fi

# Get Cloud SQL connection name
SQL_CONNECTION_NAME=$(gcloud sql instances describe ${SQL_INSTANCE_NAME} --format="value(connectionName)")
echo "SQL Connection Name: ${SQL_CONNECTION_NAME}"

# Create database if it doesn't exist
echo -e "${YELLOW}Setting up database...${NC}"
if gcloud sql databases describe ${DATABASE_NAME} --instance=${SQL_INSTANCE_NAME} 2>/dev/null; then
    echo -e "${GREEN}Database ${DATABASE_NAME} already exists${NC}"
else
    gcloud sql databases create ${DATABASE_NAME} --instance=${SQL_INSTANCE_NAME}
    echo -e "${GREEN}Database created${NC}"
fi

# Create database user if it doesn't exist
echo -e "${YELLOW}Setting up database user...${NC}"
if gcloud sql users list --instance=${SQL_INSTANCE_NAME} --format="value(name)" | grep -q "^${DATABASE_USER}$"; then
    echo -e "${YELLOW}User ${DATABASE_USER} already exists${NC}"
else
    echo -e "${YELLOW}Please enter a password for database user ${DATABASE_USER}:${NC}"
    read -s DB_PASSWORD
    echo ""
    gcloud sql users create ${DATABASE_USER} \
        --instance=${SQL_INSTANCE_NAME} \
        --password=${DB_PASSWORD}
    echo -e "${GREEN}Database user created${NC}"
fi

# Store secrets in Secret Manager
echo -e "${YELLOW}Setting up secrets...${NC}"

# Get or prompt for SECRET_KEY
if [ -f .env.prod ]; then
    SECRET_KEY=$(grep "^SECRET_KEY=" .env.prod | cut -d '=' -f2)
fi
if [ -z "$SECRET_KEY" ]; then
    echo -e "${YELLOW}Generating SECRET_KEY...${NC}"
    SECRET_KEY=$(openssl rand -hex 32)
fi

# Create/update secrets
echo -e "${YELLOW}Storing secrets in Secret Manager...${NC}"
echo -n "${SECRET_KEY}" | gcloud secrets create aether-secret-key --data-file=- --replication-policy=automatic 2>/dev/null || \
    echo -n "${SECRET_KEY}" | gcloud secrets versions add aether-secret-key --data-file=-

if [ ! -z "$DB_PASSWORD" ]; then
    echo -n "${DB_PASSWORD}" | gcloud secrets create aether-db-password --data-file=- --replication-policy=automatic 2>/dev/null || \
        echo -n "${DB_PASSWORD}" | gcloud secrets versions add aether-db-password --data-file=-
fi

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"

# Build DATABASE_URL
DATABASE_URL="postgresql+asyncpg://${DATABASE_USER}:\${DB_PASSWORD}@localhost/${DATABASE_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}"

gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME}:latest \
    --region=${REGION} \
    --platform=managed \
    --allow-unauthenticated \
    --set-cloudsql-instances=${SQL_CONNECTION_NAME} \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="POSTGRES_USER=${DATABASE_USER}" \
    --set-env-vars="POSTGRES_DB=${DATABASE_NAME}" \
    --set-env-vars="DATABASE_URL=postgresql+asyncpg://${DATABASE_USER}@localhost:5432/${DATABASE_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}" \
    --set-env-vars="ALGORITHM=HS256" \
    --set-env-vars="ACCESS_TOKEN_EXPIRE_MINUTES=30" \
    --set-env-vars="REFRESH_TOKEN_EXPIRE_DAYS=7" \
    --update-secrets="SECRET_KEY=aether-secret-key:latest,POSTGRES_PASSWORD=aether-db-password:latest" \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=10 \
    --min-instances=0 \
    --timeout=300

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run the database migration script to import your data"
echo "   ./scripts/migrate-database-to-cloud.sh"
echo ""
echo "2. Test your API:"
echo "   curl ${SERVICE_URL}/health"
echo ""
echo "3. Update your frontend FRONTEND_URL if needed"
