# LKML Assistant

A serverless application that monitors the Rust for Linux mailing list, tracks patches/PRs, and provides summaries of discussions and patch statuses.

## Project Structure

- `/infra`: CDK infrastructure code
  - `/lib`: CDK constructs for each component
  - `/bin`: CDK app entry point
- `/src`: Lambda function source code
  - `/functions`: Individual Lambda functions
  - `/models`: Shared data models and interfaces
  - `/utils`: Shared utility functions
- `/tests`: Test code
  - `/unit`: Unit tests
  - `/integration`: Integration tests

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for Lambda functions)

### Setup

1. Install dependencies:

```bash
# For CDK infrastructure
cd infra
npm install

# For Python Lambda functions
cd ../src/functions/fetch-patches
pip install -r requirements.txt
```

2. Deploy the infrastructure:

```bash
cd infra
npm run bootstrap  # Only needed once per AWS account/region
npm run deploy
```

## Features

- Monitors the Rust for Linux mailing list
- Tracks patch submissions and their statuses
- Analyzes discussions about patches
- Generates summaries of patches and discussions
- Presents information through a user-friendly dashboard

## Development

### Infrastructure

The project uses AWS CDK with TypeScript for infrastructure as code.

```bash
cd infra
npm run build   # Compile TypeScript
npm run synth   # Generate CloudFormation template
npm run diff    # Show changes between deployed stack and local code
npm run deploy  # Deploy changes to AWS
```

### Lambda Functions

Lambda functions are implemented in Python 3.9 and are deployed automatically as part of the CDK stack.

## License

[License details to be added]