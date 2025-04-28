# LKML Community Guide

LKML Community Guide is an expert companion for navigating open source communities, starting with the Rust for Linux subsystem on the Linux Kernel Mailing List (LKML). It serves as your experienced community guide, providing in-depth analysis and context around ongoing development discussions.

## Purpose

Joining and contributing to established open source communities like the Linux kernel can be daunting. This project bridges the gap by offering expert-level insights that help you understand:

- **Community dynamics**: Learn how discussions flow and decisions are made
- **Technical context**: Understand the reasoning behind arguments for and against proposals
- **Ongoing work status**: Track patches through their journey to acceptance
- **Historical context**: See how current discussions relate to past decisions

### Who This Helps

- **Newcomers to the community**: Get up to speed quickly with guided insights and explanations
- **Contributors**: Understand why your contributions might be stalled and what it would take to get them accepted
- **Reviewers**: Gain better context around what submitters are trying to achieve
- **Project observers**: Follow technical evolution without drowning in implementation details

### Key Challenges We Address

1. **Community barriers**: Established communities have implicit knowledge that's hard to acquire
2. **Context fragmentation**: Understanding requires piecing together discussions across many threads
3. **Missing perspectives**: Technical disagreements often stem from different priorities and constraints
4. **Knowledge silos**: Expertise is concentrated in long-time contributors, limiting community growth

## Core Functionality

LKML Community Guide:

1. **Collects data** from Patchwork API and lore.kernel.org to capture patches and discussions
2. **Processes content** to classify messages, extract key information, and provide context
3. **Analyzes discussions** to identify different perspectives, technical barriers, and action items
4. **Presents expert insights** tailored to different user needs and knowledge levels

## Technical Approach

This project uses a serverless architecture on AWS, allowing it to scale automatically with minimal operational overhead. The design emphasizes:

- **AI-enhanced analysis**: Machine learning to derive insights from community discussions
- **Event-driven processing**: New data triggers appropriate workflows automatically
- **Context preservation**: Connections between related discussions maintain historical context
- **Extensibility**: Modular design allows for supporting additional communities beyond Rust for Linux

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

The LKML Community Guide is designed to grow with the communities it serves. Here's how you can contribute:

### For Users

If you're interested in using the LKML Community Guide:

1. The project is currently in development, focusing first on the Rust for Linux community
2. We'll provide access details as the prototype becomes available
3. We welcome input on which communities would benefit most from this approach

### For Contributors

Want to help build the LKML Community Guide? Here's what you need:

#### Prerequisites

- Node.js (v14 or later)
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for Lambda functions)
- Docker/Podman for local testing

#### Development Setup

1. Clone this repository:

```bash
git clone https://github.com/teg/lkml-assistant.git
cd lkml-assistant
```

2. Install dependencies:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install infrastructure dependencies
cd infra
npm install
```

3. Run local tests:

```bash
make test-unit        # Run Python unit tests
make test-lambda-direct  # Test Lambda functions locally
```

4. (Optional) Deploy the infrastructure to your AWS account:

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
make fmt                # Format all code (Python and TypeScript)
make setup-hooks        # Install Git hooks for automatic formatting
```

For more details on our testing approach, see the [Local Testing Approach decision document](./docs/architecture/decisions/0003-local-testing-approach.md).

### Code Formatting

The project uses automated code formatting to maintain consistency:

- **Python**: Black formatter and flake8 linter
- **TypeScript**: Prettier formatter and ESLint linter

To format all code in the project, run:

```bash
make fmt
```

Git hooks are available to automatically format code before each commit. To set up the hooks, run:

```bash
make setup-hooks
```

## License

[License details to be added]