# 🛠️ Makefile - Helper commands for athomic

# ----- Configuration Variables -----
ROOT_DIR := .
SRC_DIR := src
TEST_DIR := tests
PYTEST = poetry run pytest

# Main package name for coverage
PACKAGE_NAME = nala
# ----------------------------
# DEFAULT TARGET
# ----------------------------
.DEFAULT_GOAL := help

# ----- Phony Targets (Avoids conflicts with file names) -----
.PHONY: help install  setup \

# ----- Main Commands -----

# 📘 Help
help: ## Shows help for available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

h: help ## Shows help for available commands


# 🚀 Setup and Run Commands
install: setup ## Alias for setup (install dependencies)
	@true

setup: ## Sets up local environment with Poetry
	@echo "--- Setting up environment with Poetry ---"
	@chmod +x bin/setup.sh && source bin/setup.sh

run: ## Runs the project locally with reload (Uvicorn)
	@echo "🚀 Running the project..."
	@poetry run uvicorn src.nala.api.main:app --host 0.0.0.0 --port 8000 --reload

# 🔐 Security
secrets: secrets-scan ## Alias for secrets-scan
	@true

secrets-scan: ## Runs detect-secrets to check for committed secrets
	@echo "--- Checking secrets with detect-secrets ---"
	@poetry run detect-secrets scan --baseline .secrets.baseline

bandit: ## Runs static security analysis with Bandit
	@echo "--- Checking security with Bandit ---"
	@poetry run bandit -r src/ -x tests/ -ll # Shows only medium/high issues


# ----------------------------
# VARIABLES
# ----------------------------
COMPOSE_ALL=infra/docker-compose.all.yml

# ----------------------------
# GENERAL INFRA
# ----------------------------

infra-up:
	@echo "docker compose -f $(COMPOSE_ALL) up -d --remove-orphans --force-recreate"
	@docker compose -f $(COMPOSE_ALL) up -d --remove-orphans --force-recreate
	@echo "Infrastructure containers started successfully!"

infra-down:
	@echo "docker compose -f $(COMPOSE_ALL) down --remove-orphans --volumes"
	@docker compose -f $(COMPOSE_ALL) down --remove-orphans --volumes
	@echo "Infrastructure containers stopped and volumes removed!"

app-up:
	@echo "docker compose up -d --remove-orphans --force-recreate"
	@docker compose up -d --remove-orphans --force-recreate
	@echo "Application containers started successfully!"

app-down:
	@echo "docker compose down --remove-orphans"
	@docker compose down --remove-orphans
	@echo "Infrastructure containers stopped and volumes removed!"

# ----------------------------
# PARAMETER HANDLING
# ----------------------------

-o%: # Captures -o parameter and sets OUTPUT variable
	@$(eval OUTPUT=-o $*)

--output%: # Captures --output parameter and sets OUTPUT variable
	@$(eval OUTPUT=--output $*)

# ----------------------------

# Ignore "No rule to make target" errors
%:
	@:
