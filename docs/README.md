# Documentation

This directory contains comprehensive technical documentation for KnowledgeWeaver, organized by topic.

## Directory Structure

```
docs/
├── architecture/     # Architecture diagrams and design documents
├── deployment/       # AWS and deployment guides
├── database/         # Database setup and optimization guides
├── observability/    # Monitoring and observability documentation
├── development/      # Development and testing guides
└── security/         # Security best practices and guidelines
```

## Architecture

**Location**: `architecture/`

### System Architecture

- **Interactive Diagrams** (Recommended)
  - `architecture-diagram-cn.html` - Chinese interactive architecture diagram (D3.js)
  - `architecture-diagram-en.html` - English interactive architecture diagram (D3.js)
  - Open in browser for interactive visualization with hover effects

- **Static Images**
  - `architecture-cn.png` - Chinese architecture diagram (PNG, 1.6MB)
  - `architecture-en.png` - English architecture diagram (PNG, 1.6MB)
  - Used in README files for quick reference

### AWS Cloud Architecture

- **Interactive Diagrams** (Recommended)
  - `aws-architecture-diagram-cn.html` - Chinese AWS cloud architecture (D3.js)
  - `aws-architecture-diagram-en.html` - English AWS cloud architecture (D3.js)
  - Visualizes VPC, subnets, EKS cluster, pods, and AWS managed services
  - Open in browser for interactive visualization with hover effects

- **Documentation**
  - `README.md` - Architecture overview and cost estimates
  - `ARCHITECTURE_UPDATES.md` - Version 2.0 changelog (demo environment)

## Deployment

**Location**: `deployment/`

- `AWS_DEPLOYMENT_GUIDE.md` - Complete AWS deployment guide for KnowledgeWeaver
- `AWS_IAM_CLI_SETUP_GUIDE.md` - AWS IAM and CLI setup instructions
- `AWS_EKS_DEPLOYMENT.md` - AWS EKS deployment detailed guide
- `EKS_CONCEPTS_GUIDE.md` - EKS concepts and best practices
- `EKS_IRSA_FIX.md` - EKS IRSA (IAM Roles for Service Accounts) troubleshooting
- `DOCKER_IMAGE_BUILD.md` - Docker image build and registry guide
- `DEPLOYMENT_READINESS.md` - Deployment readiness checklist and validation

## Database

**Location**: `database/`

- `NEO4J_GUIDE.md` - Neo4j setup, configuration, and graph algorithms guide

## Observability

**Location**: `observability/`

- `LANGFUSE_GUIDE.md` - Langfuse observability platform complete guide
- `PHOENIX_INTEGRATION.md` - Phoenix integration for LLM observability
- `OBSERVABILITY_COMPARISON.md` - Comparison of observability solutions
- `OBSERVABILITY_WORKFLOW.md` - Observability workflow and best practices
- `TEST_LANGFUSE.md` - Langfuse testing guide

## Development

**Location**: `development/`

- `PROJECT_STRUCTURE.md` - Project structure and module organization
- `TEST_SUITE.md` - Testing framework and test suite documentation
- `CONFIGURATION_REVIEW.md` - Configuration management and environment setup guide

## Security

**Location**: `security/`

- `SECURITY_GUIDE.md` - Security best practices and guidelines

## Quick Links

### Getting Started
1. Start with [Project Structure](development/PROJECT_STRUCTURE.md) to understand the codebase
2. Review [Architecture Diagrams](architecture/) for system overview
3. Follow [AWS Deployment Guide](deployment/AWS_DEPLOYMENT_GUIDE.md) for production deployment

### Development
1. Check [Test Suite](development/TEST_SUITE.md) for testing guidelines
2. Review [Security Guide](security/SECURITY_GUIDE.md) before implementing features

### Operations
1. Set up [Neo4j](database/NEO4J_GUIDE.md) for graph database
2. Configure [Langfuse](observability/LANGFUSE_GUIDE.md) or [Phoenix](observability/PHOENIX_INTEGRATION.md) for observability
3. Compare [Observability Solutions](observability/OBSERVABILITY_COMPARISON.md) to choose the right tool

## Notes

- All interactive HTML diagrams provide the best visualization experience
- PNG images are optimized for README display
- All documentation uses Markdown format for easy maintenance and version control
- Documentation is updated regularly to reflect the latest system changes
