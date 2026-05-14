#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/sagunto_hub_bot_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $FILENAME"
docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sagunto_bot_user}" \
  "${POSTGRES_DB:-sagunto_hub_bot}" \
  | gzip > "$FILENAME"

echo "Backup complete: $FILENAME"

# Restore with:
# gunzip -c <file> | docker compose exec -T postgres psql \
#   -U sagunto_bot_user sagunto_hub_bot
