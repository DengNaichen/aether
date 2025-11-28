#!/bin/bash

# Aether - Backup Local Database
# Quick script to backup your local PostgreSQL database

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DATABASE_USER="aether_user"
DATABASE_NAME="aether_db"
BACKUP_DIR="./backups"
BACKUP_FILE="${BACKUP_DIR}/aether_db_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${GREEN}=== Aether Local Database Backup ===${NC}"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Check if Docker is running
if ! docker-compose ps db | grep -q "Up"; then
    echo -e "${YELLOW}Starting database container...${NC}"
    docker-compose up -d db
    sleep 3
fi

# Create backup
echo -e "${YELLOW}Creating backup...${NC}"
docker-compose exec -T db pg_dump -U ${DATABASE_USER} -d ${DATABASE_NAME} --clean --if-exists > ${BACKUP_FILE}

# Check if backup was successful
if [ -s ${BACKUP_FILE} ]; then
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "  Location: ${BACKUP_FILE}"
    echo "  Size: $(du -h ${BACKUP_FILE} | cut -f1)"
else
    echo -e "${RED}✗ Backup failed${NC}"
    rm -f ${BACKUP_FILE}
    exit 1
fi
