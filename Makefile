.PHONY: test test-unit test-integration test-local test-lambda-direct test-lambda-localstack deploy clean-local format test-post-deploy test-post-deploy-dev test-post-deploy-staging test-post-deploy-prod

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
	
# Run only direct Lambda invocation tests (no LocalStack required)
test-lambda-direct:
	./scripts/run_direct_lambda_tests.sh

# Run only LocalStack Lambda tests
test-lambda-localstack:
	./scripts/run_local_tests.sh

# Deploy to dev environment
deploy:
	cd infra && npm run deploy

# Clean up local test environment
clean-local:
	./scripts/clean_local_test_env.sh --stop-containers
	
# Format Python code with Black
format:
	chmod +x ./scripts/format.sh
	./scripts/format.sh
	
# Run post-deployment tests against the default (dev) environment
test-post-deploy:
	chmod +x ./scripts/post_deploy_test_runner.sh
	./scripts/post_deploy_test_runner.sh dev

# Run post-deployment tests against dev environment
test-post-deploy-dev:
	chmod +x ./scripts/post_deploy_test_runner.sh
	./scripts/post_deploy_test_runner.sh dev

# Run post-deployment tests against staging environment
test-post-deploy-staging:
	chmod +x ./scripts/post_deploy_test_runner.sh
	./scripts/post_deploy_test_runner.sh staging

# Run post-deployment tests against production environment
test-post-deploy-prod:
	chmod +x ./scripts/post_deploy_test_runner.sh
	./scripts/post_deploy_test_runner.sh prod