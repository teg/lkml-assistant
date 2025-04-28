# Using Podman with LKML Assistant

This document provides instructions for setting up and running the LKML Assistant application with Podman instead of Docker.

## Prerequisites

- Podman installed and running on your machine
- Python 3.9+
- AWS CLI
- podman-compose (optional)

## Installation

### Install Podman

Follow the official Podman installation instructions for your operating system: https://podman.io/docs/installation

### Install podman-compose (Optional)

You can install podman-compose using pip:

```bash
pip install podman-compose
```

## Running Local Tests

### Using Manual Podman Setup

1. Start the DynamoDB container:

```bash
podman run -d --name lkml-assistant-dynamodb -p 8000:8000 amazon/dynamodb-local:latest -jar DynamoDBLocal.jar -sharedDb -inMemory
```

2. Run the integration tests:

```bash
cd /path/to/lkml-assistant
export PATH=$PATH:$HOME/Library/Python/3.9/bin  # Adjust path as needed
python -m pytest tests/integration/test_local_dynamodb.py -v
```

3. Stop and remove the container when done:

```bash
podman stop lkml-assistant-dynamodb
podman rm lkml-assistant-dynamodb
```

### Using Podman Compose

If you prefer to use podman-compose:

1. Create or modify your docker-compose.yml file:

```yaml
services:
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    container_name: lkml-assistant-dynamodb
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb -inMemory"

  localstack:
    image: localstack/localstack:latest
    container_name: lkml-assistant-localstack
    ports:
      - "4566:4566"
    environment:
      - SERVICES=lambda,sqs,events,logs,cloudwatch
      - DEBUG=1
```

2. Start the services:

```bash
podman-compose up -d
```

3. Run the tests:

```bash
python -m pytest tests/integration/test_local_dynamodb.py -v
```

4. Stop and remove the containers when done:

```bash
podman-compose down
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors with DynamoDB or other AWS services:

1. Make sure you're using the correct endpoint:
   - DynamoDB: http://localhost:8000
   - LocalStack: http://localhost:4566

2. Use these test credentials:
   - AWS_ACCESS_KEY_ID: test
   - AWS_SECRET_ACCESS_KEY: test
   - AWS_DEFAULT_REGION: us-east-1

### Container Naming Conflicts

If you get errors about containers already existing:

```bash
podman rm -f lkml-assistant-dynamodb lkml-assistant-localstack
```

### Network Issues

If containers can't communicate with each other:

1. Create a custom network:
   ```bash
   podman network create lkml-assistant-network
   ```

2. Run containers on this network:
   ```bash
   podman run --network lkml-assistant-network ...
   ```