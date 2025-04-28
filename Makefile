.PHONY: test test-unit test-integration test-local deploy clean-local

# Run all tests
test:
	./scripts/run_tests.sh

# Run unit tests only
test-unit:
	./scripts/run_tests.sh python-unit

# Run integration tests against real AWS (skip by default)
test-integration:
	./scripts/run_tests.sh python-integration

# Run local integration tests against Docker containers
test-local:
	./scripts/run_local_tests.sh

# Deploy to dev environment
deploy:
	cd infra && npm run deploy

# Clean up local test environment
clean-local:
	./scripts/clean_local_test_env.sh --stop-containers