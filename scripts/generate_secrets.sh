#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

if [ ! -f "$EXAMPLE_FILE" ]; then
  echo "Error: $EXAMPLE_FILE not found." >&2
  exit 1
fi

if [ -f "$ENV_FILE" ]; then
  echo ".env already exists. Delete it first if you want to regenerate secrets."
  exit 0
fi

POSTGRES_PASSWORD=$(openssl rand -hex 32)

cp "$EXAMPLE_FILE" "$ENV_FILE"
# Replace CHANGE_ME placeholders with the generated password
sed -i "s/CHANGE_ME/$POSTGRES_PASSWORD/g" "$ENV_FILE"

echo "Generated .env with a random POSTGRES_PASSWORD."
echo "Edit .env and fill in TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID, and the TOPIC_*_ID values."
