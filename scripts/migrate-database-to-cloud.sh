#!/bin/bash

# Aether - Migrate Local Database to Cloud SQL
# This script exports your local PostgreSQL data and imports it to Cloud SQL

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
SQL_INSTANCE_NAME="aether-db-instance"
DATABASE_NAME="aether_db"
DATABASE_USER="aether_user"
BACKUP_FILE="aether_db_backup_$(date +%Y%m%d_%H%M%S).sql"
TEMP_BUCKET="gs://${PROJECT_ID}-db-migration"

echo -e "${GREEN}=== Aether Database Migration to Cloud SQL ===${NC}"
echo ""

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Starting local Docker containers...${NC}"
    docker-compose up -d
    sleep 5
fi

# Step 1: Export local database
echo -e "${YELLOW}Step 1: Exporting local database...${NC}"
docker-compose exec -T db pg_dump -U ${DATABASE_USER} -d ${DATABASE_NAME} --clean --if-exists > ${BACKUP_FILE}

if [ ! -s ${BACKUP_FILE} ]; then
    echo -e "${RED}Error: Backup file is empty${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Local database exported to ${BACKUP_FILE}${NC}"
echo "  File size: $(du -h ${BACKUP_FILE} | cut -f1)"
echo ""

# Step 2: Check if Cloud SQL instance exists
echo -e "${YELLOW}Step 2: Checking Cloud SQL instance...${NC}"
if ! gcloud sql instances describe ${SQL_INSTANCE_NAME} --format="value(name)" 2>/dev/null; then
    echo -e "${RED}Error: Cloud SQL instance ${SQL_INSTANCE_NAME} not found${NC}"
    echo "Please run ./scripts/deploy-to-cloud-run.sh first"
    exit 1
fi
echo -e "${GREEN}✓ Cloud SQL instance found${NC}"
echo ""

# Step 3: Create temporary GCS bucket for import
echo -e "${YELLOW}Step 3: Preparing Cloud Storage for import...${NC}"
if ! gsutil ls ${TEMP_BUCKET} 2>/dev/null; then
    gsutil mb -p ${PROJECT_ID} ${TEMP_BUCKET}
    echo -e "${GREEN}✓ Created temporary bucket: ${TEMP_BUCKET}${NC}"
else
    echo -e "${GREEN}✓ Using existing bucket: ${TEMP_BUCKET}${NC}"
fi
echo ""

# Step 4: Upload backup to GCS
echo -e "${YELLOW}Step 4: Uploading backup to Cloud Storage...${NC}"
gsutil cp ${BACKUP_FILE} ${TEMP_BUCKET}/
echo -e "${GREEN}✓ Backup uploaded${NC}"
echo ""

# Step 5: Import to Cloud SQL
echo -e "${YELLOW}Step 5: Importing to Cloud SQL...${NC}"
echo "This may take several minutes depending on your database size..."

gcloud sql import sql ${SQL_INSTANCE_NAME} ${TEMP_BUCKET}/${BACKUP_FILE} \
    --database=${DATABASE_NAME} \
    --quiet

echo -e "${GREEN}✓ Database imported successfully${NC}"
echo ""

# Step 6: Verify import
echo -e "${YELLOW}Step 6: Verifying import...${NC}"
TABLE_COUNT=$(gcloud sql connect ${SQL_INSTANCE_NAME} --user=${DATABASE_USER} --database=${DATABASE_NAME} --quiet <<EOF | grep -c "^"
\dt
\q
EOF
)

if [ ${TABLE_COUNT} -gt 0 ]; then
    echo -e "${GREEN}✓ Verification successful - found ${TABLE_COUNT} tables${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify table count (may require manual check)${NC}"
fi
echo ""

# Step 7: Cleanup
echo -e "${YELLOW}Step 7: Cleanup...${NC}"
read -p "Do you want to delete the backup from Cloud Storage? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gsutil rm ${TEMP_BUCKET}/${BACKUP_FILE}
    echo -e "${GREEN}✓ Backup deleted from Cloud Storage${NC}"
else
    echo -e "${YELLOW}Backup kept at: ${TEMP_BUCKET}/${BACKUP_FILE}${NC}"
fi

read -p "Do you want to delete the local backup file? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm ${BACKUP_FILE}
    echo -e "${GREEN}✓ Local backup deleted${NC}"
else
    echo -e "${YELLOW}Local backup kept at: ${BACKUP_FILE}${NC}"
fi
echo ""

echo -e "${GREEN}=== Database Migration Complete! ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test your Cloud Run service:"
echo "   SERVICE_URL=\$(gcloud run services describe aether-api --region=us-central1 --format='value(status.url)')"
echo "   curl \${SERVICE_URL}/health"
echo ""
echo "2. Verify database connection from Cloud Run"
echo ""
echo "3. Update your frontend to use the Cloud Run URL"
