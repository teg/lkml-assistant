.PHONY: test test-unit test-integration test-local test-lambda-direct test-lambda-localstack deploy clean-local format fmt setup-hooks test-post-deploy test-post-deploy-dev test-post-deploy-staging test-post-deploy-prod

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

# Create Lambda layer with dependencies
create-lambda-layer:
	chmod +x ./scripts/create_lambda_layer.sh
	./scripts/create_lambda_layer.sh

# Deploy to dev environment
deploy: create-lambda-layer
	cd infra && AWS_PROFILE=lkml-assistant npm run deploy -- -c environment=dev

# Deploy and test the deployment
deploy-and-test: deploy
	export AWS_PROFILE=lkml-assistant && make test-post-deploy-dev

# Clean up local test environment
clean-local:
	./scripts/clean_local_test_env.sh --stop-containers
	
# Format Python code with Black (keeping for backward compatibility)
format:
	chmod +x ./scripts/format.sh
	./scripts/format.sh

# Format all code in the project (Python and TypeScript)
fmt:
	chmod +x ./scripts/format_all.sh
	./scripts/format_all.sh
	
# Set up Git hooks to run formatting before commits
setup-hooks:
	chmod +x ./scripts/setup_git_hooks.sh
	./scripts/setup_git_hooks.sh
	
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