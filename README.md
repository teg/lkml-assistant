# LKML Assistant

LKML Assistant is a specialized tool that monitors the Rust for Linux subsystem development on the Linux Kernel Mailing List (LKML). It provides automated tracking, analysis, and insights into the patch review process.

## Purpose

Rust for Linux is an ongoing effort to bring Rust language support to the Linux kernel. This project helps developers, contributors, and observers stay informed about:

- **Patch progression**: Track patches from submission through the review process
- **Discussion threads**: Follow technical discussions and issues raised during review
- **Review status**: Identify patches requiring attention or approaching acceptance
- **Development trends**: Observe patterns in contribution activity and subsystem evolution

The goal is to reduce friction in the Rust for Linux review process by providing clear visibility into patch status, addressing common workflow challenges:

1. **Information overload**: The high volume of kernel discussions makes following specific patches difficult
2. **Discussion fragmentation**: Patch feedback spreads across multiple emails and threads
3. **Status uncertainty**: Determining a patch's current state requires manually checking multiple sources
4. **Context switching**: Contributors need to constantly monitor mailing lists to catch relevant updates

## Core Functionality

LKML Assistant:

1. **Collects data** from Patchwork API and lore.kernel.org to capture patches and discussions
2. **Processes content** to classify messages, extract key information, and track status changes
3. **Builds relationships** between patches, series, and discussions to create a complete picture
4. **Presents insights** in useful formats for different stakeholders

## Technical Approach

This project uses a serverless architecture on AWS, allowing it to scale automatically with minimal operational overhead. The design emphasizes:

- **Event-driven processing**: New data triggers appropriate workflows automatically
- **High resilience**: Fault-tolerant design with comprehensive error handling
- **Low operational costs**: Pay-only-for-usage serverless model minimizes expenses
- **Extensibility**: Modular design allows for adding new data sources and functionality

For detailed technical information, see:
- [Architecture Documentation](./docs/architecture/)
- [Implementation Plan](./docs/implementation/)

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
- `/docs`: Project documentation
  - `/architecture`: System architecture details
  - `/implementation`: Implementation plan and progress
  - `/adr`: Architecture Decision Records

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

### Testing

The project uses a multi-faceted approach to testing:

```bash
make test               # Run all tests
make test-unit          # Run unit tests only
make test-lambda-direct # Run direct Lambda invocation tests
make test-local         # Run tests with Docker/Podman containers
make format             # Format Python code with Black
```

For more details on our testing approach, see the [Local Testing Approach decision document](./docs/architecture/decisions/0003-local-testing-approach.md).

## License

[License details to be added]