# Architecture Diagrams

This directory contains interactive and static architecture diagrams for KnowledgeWeaver.

## System Architecture

Shows the core processing pipeline and components of KnowledgeWeaver.

### Interactive Diagrams (Recommended)

- **[System Architecture - English](architecture-diagram-en.html)** (Open in browser)
  - Interactive D3.js visualization
  - Hover effects and visual feedback
  - Shows: Document processing → Entity extraction → Storage → Q&A pipeline

- **[System Architecture - Chinese](architecture-diagram-cn.html)** (Open in browser)
  - 交互式 D3.js 可视化
  - 悬停效果和视觉反馈
  - 展示：文档处理 → 实体提取 → 存储 → 问答流程

### Static Images

- `architecture-en.png` - Static version for README (1.6MB)
- `architecture-cn.png` - 静态版本用于 README (1.6MB)

### Components Shown

1. **Input Layer**: Documents (txt/pdf)
2. **Processing Layer**:
   - Document chunking
   - LLM entity extraction
   - Knowledge merging & normalization
3. **Storage Layer**:
   - JSON file storage
   - ChromaDB vector database
4. **Service Layer**:
   - FastAPI backend
   - Hybrid retriever
   - QA engine
5. **Frontend Layer**:
   - D3.js knowledge graph visualization
   - Chat UI

---

## AWS Cloud Architecture

Shows the production deployment architecture on AWS.

### Interactive Diagrams (Recommended)

- **[AWS Architecture - English](aws-architecture-diagram-en.html)** (Open in browser)
  - Interactive D3.js visualization
  - Hover effects and visual feedback
  - Shows: VPC, subnets, ECS Fargate, EC2, AWS managed services

- **[AWS Architecture - Chinese](aws-architecture-diagram-cn.html)** (Open in browser)
  - 交互式 D3.js 可视化
  - 悬停效果和视觉反馈
  - 展示：VPC、子网、ECS Fargate、EC2、AWS 托管服务

### Architecture Highlights

#### Network Architecture
- **VPC (10.0.0.0/16)** with public and private subnets
- **Public Subnet (10.0.1.0/24)**: ALB, NAT Gateway, Internet Gateway
- **Private Subnet (10.0.2.0/24)**: ECS Fargate, Neo4j EC2
- **Multi-AZ deployment** for high availability

#### Compute Layer
- **ECS Fargate**: Serverless container platform for FastAPI service
  - Auto-scaling based on load
  - Deployed across 2 availability zones
- **Neo4j EC2 (t3.medium)**: Graph database
  - Primary in AZ1, Standby in AZ2
  - Private subnet for security

#### Storage & Data
- **S3**: Document storage
- **ECR**: Docker container registry
- **RDS PostgreSQL**: Phoenix/Langfuse observability backend

#### Management & Monitoring
- **CloudWatch**: Logs, metrics, and dashboards
- **Secrets Manager**: Secure credential storage
- **SNS**: Alert notifications
- **CloudTrail**: Audit logging

#### Security Features
- ✅ Application in private subnet (no public IP)
- ✅ ALB in public subnet (only entry point)
- ✅ Security groups with least privilege
- ✅ NAT Gateway for outbound traffic only
- ✅ Secrets Manager for credential management

### Cost Estimation

| Service | Monthly Cost |
|---------|--------------|
| ECS Fargate | ~$30-50 |
| ALB | ~$20 |
| Neo4j EC2 (t3.medium) | ~$30 |
| S3 | ~$1-5 |
| CloudWatch + Phoenix | ~$10-20 |
| Secrets Manager | ~$1-2 |
| **Total** | **~$92-128** |

*Note: Costs can be reduced by ~30% using Reserved Instances*

---

## How to View Interactive Diagrams

1. Download or clone the repository
2. Open the HTML files in a web browser:
   ```bash
   open architecture-diagram-en.html
   # or
   open aws-architecture-diagram-en.html
   ```
3. Interact with the diagram:
   - Hover over components for visual feedback
   - Explore the connections and data flow

## Related Documentation

- [AWS Deployment Guide](../deployment/AWS_DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Project Structure](../development/PROJECT_STRUCTURE.md) - Code organization
- [Neo4j Guide](../database/NEO4J_GUIDE.md) - Graph database setup
- [Observability Guide](../observability/PHOENIX_INTEGRATION.md) - Monitoring and tracing

---

**Last Updated**: 2026-01-28
**Maintainer**: Sheldon
