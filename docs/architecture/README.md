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
   - LLM entity extraction (Claude CLI / Gemini API)
   - Knowledge merging & normalization
3. **Storage Layer**:
   - **Neo4j** graph database (knowledge graph storage)
   - **ChromaDB** vector database (semantic search)
4. **Service Layer**:
   - FastAPI backend
   - Hybrid retriever (KG + RAG)
   - QA engine
5. **Frontend Layer**:
   - D3.js knowledge graph visualization
   - Chat UI

---

## AWS Cloud Architecture

Shows the **demo/interview deployment** architecture on AWS EKS.

### Interactive Diagrams (Recommended)

- **[AWS Architecture - English](aws-architecture-diagram-en.html)** (Open in browser)
  - Interactive D3.js visualization
  - Hover effects and visual feedback
  - Shows: VPC, subnets, EKS cluster, pods, AWS managed services

- **[AWS Architecture - Chinese](aws-architecture-diagram-cn.html)** (Open in browser)
  - 交互式 D3.js 可视化
  - 悬停效果和视觉反馈
  - 展示：VPC、子网、EKS 集群、Pod、AWS 托管服务

### Architecture Highlights

#### Network Architecture
- **VPC (10.0.0.0/16)** with public and private subnets
- **Public Subnet (10.0.1.0/24)**: Internet Gateway, ALB, NAT Gateway
- **Private Subnet (10.0.2.0/24)**: EKS worker nodes and pods

#### Compute Layer (EKS Kubernetes)
- **Namespace**: `demo` (single environment)
- **API Pod (FastAPI)**: 1 replica (auto-scales 1-3)
  - Resource limits: 512Mi-1Gi memory, 250m-1000m CPU
  - Deployed on Worker Node 1
- **Neo4j Pod**: Graph database (StatefulSet)
  - Deployed on Worker Node 2
  - EBS persistent storage
- **Worker Nodes**: 2x t3.medium instances
- **Observability** (optional): Phoenix, Langfuse, PostgreSQL pods

#### Storage & Data
- **S3**: Document storage
- **ECR**: Docker container registry
- **EBS Volumes**: Persistent storage for Neo4j and PostgreSQL
- **RDS PostgreSQL** (optional): Observability backend

#### Management & Monitoring
- **CloudWatch**: Logs, metrics, and dashboards
- **Secrets Manager**: Secure credential storage
- **SNS**: Alert notifications
- **CloudTrail**: Audit logging

#### Security Features
- ✅ Pods in private subnet (no public IP)
- ✅ IRSA (IAM Roles for Service Accounts) using OIDC
- ✅ Security groups with least privilege
- ✅ NAT Gateway for outbound traffic only
- ✅ Secrets Manager for credential management

#### Public Access Options

Three ways to access the API:

1. **LoadBalancer Service** (recommended for demo)
   - AWS NLB automatically provisioned
   - Public URL: `http://xxx.elb.amazonaws.com`
   - Cost: ~$20-30/month

2. **Ingress + ALB Controller**
   - Advanced routing, SSL support
   - Cost: ~$25-40/month

3. **NodePort**
   - Direct node access
   - Cost: $0 (testing only)

See [Public Access Guide](../../deploy/kubernetes/PUBLIC_ACCESS_GUIDE.md) for details.

### Cost Estimation (Demo Environment)

| Service | Monthly Cost |
|---------|--------------|
| EKS Control Plane | $73 |
| Worker Nodes (2x t3.medium) | ~$60 |
| NLB (LoadBalancer) | ~$20 |
| EBS Volumes (50GB) | ~$5 |
| S3 + ECR | ~$5 |
| CloudWatch | ~$10 |
| **Total** | **~$173** |

**Cost Optimization:**
- Stop cluster when not in use: Save ~$60/month
- Use Spot instances: Save ~40% on worker nodes
- Use t3.small instead of t3.medium: Save ~$30/month
- **Demo cost (8 hours/day)**: ~$60-80/month

---

## Recent Updates

**Version 2.0 (2026-01-29)** - Demo/Interview Configuration

Key changes:
- ✅ Updated to demo environment (namespace: `demo`, 1 API pod)
- ✅ Simplified deployment (removed overlays)
- ✅ Added 3 public access methods (LoadBalancer/Ingress/NodePort)
- ✅ Corrected storage layer (Neo4j instead of JSON)
- ✅ Improved architecture diagram visuals
- ✅ 60% cost reduction (~$60-80/month for 8hrs/day)

See [Architecture Updates](ARCHITECTURE_UPDATES.md) for full changelog.

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

### Deployment
- [AWS Deployment Guide](../deployment/AWS_DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [EKS Deployment Guide](../deployment/AWS_EKS_DEPLOYMENT.md) - EKS cluster setup
- [Public Access Guide](../../deploy/kubernetes/PUBLIC_ACCESS_GUIDE.md) - How to access via public IP
- [Kubernetes README](../../deploy/kubernetes/README.md) - Quick deploy guide
- [EKS IRSA Fix](../deployment/EKS_IRSA_FIX.md) - OIDC and IAM Roles for Service Accounts

### Database & Storage
- [Neo4j Guide](../database/NEO4J_GUIDE.md) - Graph database setup and algorithms

### Development
- [Project Structure](../development/PROJECT_STRUCTURE.md) - Code organization
- [Configuration Review](../development/CONFIGURATION_REVIEW.md) - Environment setup

### Observability
- [Phoenix Integration](../observability/PHOENIX_INTEGRATION.md) - Monitoring and tracing
- [Langfuse Guide](../observability/LANGFUSE_GUIDE.md) - LLM observability

---

**Last Updated**: 2026-01-29
**Maintainer**: Sheldon
