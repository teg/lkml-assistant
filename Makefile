.PHONY: build test lint fmt clean

# Project settings
PYTHON = python3
PIP = pip3
PROJECT_NAME = lkml-assistant

# Directories
SRC_DIR = src
TESTS_DIR = tests
INFRA_DIR = infra

# CDK commands
build:
	cd $(INFRA_DIR) && npm run build

synth:
	cd $(INFRA_DIR) && npm run synth

deploy:
	cd $(INFRA_DIR) && npm run deploy

# Python commands
install-deps:
	cd $(INFRA_DIR) && npm install
	$(PIP) install -r requirements.txt

# Testing commands
test: test-all

test-all:
	./scripts/run_tests.sh

test-python: test-python-lint test-python-unit test-python-integration

test-python-lint:
	./scripts/run_tests.sh python-lint

test-python-unit:
	./scripts/run_tests.sh python-unit

test-python-integration:
	./scripts/run_tests.sh python-integration

test-typescript:
	./scripts/run_tests.sh typescript-tests

test-cdk:
	./scripts/run_tests.sh cdk-synth

# Code quality commands
lint:
	cd $(INFRA_DIR) && npm run lint
	flake8 $(SRC_DIR) $(TESTS_DIR)

fmt:
	cd $(INFRA_DIR) && npm run format
	black $(SRC_DIR) $(TESTS_DIR)

# Code coverage
coverage:
	$(PYTHON) -m pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=term $(TESTS_DIR)

clean:
	rm -rf $(INFRA_DIR)/cdk.out
	rm -rf $(INFRA_DIR)/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete