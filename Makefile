COMPOSE = docker compose
BACKUP_DIR = backups
VENV = $(HOME)/.venvs/sagunto-hub-bot
PYTHON = $(VENV)/bin/python3

.PHONY: secrets install build up down logs db-shell backup test lint

secrets:
	@bash scripts/generate_secrets.sh

install:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip -q
	$(PYTHON) -m pip install -r requirements.txt

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
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check bot/ tests/
