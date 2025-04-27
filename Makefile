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

test:
	$(PYTHON) -m unittest discover -s $(TESTS_DIR)

test-unit:
	$(PYTHON) -m unittest discover -s $(TESTS_DIR)/unit

lint:
	cd $(INFRA_DIR) && npm run lint
	flake8 $(SRC_DIR) $(TESTS_DIR)

fmt:
	cd $(INFRA_DIR) && npm run format
	black $(SRC_DIR) $(TESTS_DIR)

clean:
	rm -rf $(INFRA_DIR)/cdk.out
	rm -rf $(INFRA_DIR)/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete