COMPOSE = docker compose
BACKUP_DIR = backups

.PHONY: secrets build up down logs db-shell backup test lint

secrets:
	@bash scripts/generate_secrets.sh

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f bot

db-shell:
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-sagunto_bot_user} -d $${POSTGRES_DB:-sagunto_hub_bot}

backup:
	@bash scripts/backup_postgres.sh

test:
	pytest tests/ -v

lint:
	ruff check bot/ tests/
