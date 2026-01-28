# KnowledgeWeaver AWS 部署指南

## 🎯 部署目标

为 AI Ops Engineer 面试准备，展示以下核心能力：
- ✅ **AWS 架构设计**：云原生架构，服务选型与网络设计
- ✅ **可观测性 (Observability)**：集成 Phoenix + CloudWatch，全链路追踪
- ✅ **IaC (Terraform)**：基础设施即代码，版本化管理

## 📐 架构设计

### 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                  │  │
│  │                                                        │  │
│  │  ┌─────────────────┐      ┌─────────────────┐        │  │
│  │  │  Public Subnet  │      │ Private Subnet  │        │  │
│  │  │  10.0.1.0/24    │      │  10.0.2.0/24    │        │  │
│  │  │                 │      │                 │        │  │
│  │  │  ┌───────────┐  │      │  ┌───────────┐ │        │  │
│  │  │  │ ALB       │  │      │  │ ECS       │ │        │  │
│  │  │  │ (FastAPI) │──┼──────┼─▶│ Fargate   │ │        │  │
│  │  │  └───────────┘  │      │  │ Service   │ │        │  │
│  │  │                 │      │  └───────────┘ │        │  │
│  │  │  ┌───────────┐  │      │                 │        │  │
│  │  │  │ NAT       │  │      │  ┌───────────┐ │        │  │
│  │  │  │ Gateway   │◀─┼──────┼──│ Neo4j EC2 │ │        │  │
│  │  │  └───────────┘  │      │  └───────────┘ │        │  │
│  │  └─────────────────┘      └─────────────────┘        │  │
│  │                                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  S3 Bucket   │  │  CloudWatch  │  │  Secrets     │     │
│  │  (Documents) │  │  (Logs/      │  │  Manager     │     │
│  │              │  │   Metrics)   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Phoenix/Langfuse (RDS)                   │  │
│  │         Observability & Tracing Backend               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 服务选型理由

| 服务 | 选择 | 理由 | 成本估算 |
|------|------|------|----------|
| **应用运行** | ECS Fargate | 无服务器，自动扩展，无需管理EC2 | ~$30-50/月 |
| **负载均衡** | ALB | 支持路径路由，健康检查，SSL终止 | ~$20/月 |
| **图数据库** | Neo4j on EC2 | Neo4j AuraDB太贵，EC2可控成本 | ~$30/月 (t3.medium) |
| **文档存储** | S3 | 高可用，低成本，自动备份 | ~$1-5/月 |
| **可观测性** | CloudWatch + Phoenix | 原生集成，项目已有Phoenix | ~$10-20/月 |
| **密钥管理** | Secrets Manager | 自动轮换，审计日志 | ~$1-2/月 |
| **IaC** | Terraform | 版本化，可重复部署 | 免费 |

**总成本：约 $92-128/月** (可通过Reserved Instance降低30%)

## 🔧 部署步骤

### 前置要求

```bash
# 1. 安装工具
brew install terraform awscli

# 2. 配置AWS凭证
aws configure
# AWS Access Key ID: 你的Key
# AWS Secret Access Key: 你的Secret
# Default region: ap-southeast-2  (Sydney - 新西兰最近)
# Default output format: json

# 3. 验证配置
aws sts get-caller-identity
```

### Step 1: 克隆仓库并准备

```bash
cd ~/Github/KnowledgeWeaver
git checkout -b aws-deployment

# 创建Terraform目录
mkdir -p terraform/modules/{vpc,ecs,neo4j,observability}
```

### Step 2: 部署基础设施 (Terraform)

```bash
cd terraform

# 初始化
terraform init

# 查看计划
terraform plan -out=tfplan

# 部署（约5-10分钟）
terraform apply tfplan
```

### Step 3: 部署应用

```bash
# 构建并推送Docker镜像
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com

docker build -t knowledgeweaver:latest .
docker tag knowledgeweaver:latest <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver:latest
docker push <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver:latest

# 更新ECS服务
aws ecs update-service \
  --cluster knowledgeweaver \
  --service knowledgeweaver-api \
  --force-new-deployment
```

### Step 4: 配置可观测性

```bash
# Phoenix已集成在项目中，只需配置环境变量
# 在ECS Task Definition中添加：
PHOENIX_COLLECTOR_ENDPOINT=https://phoenix.your-domain.com
PHOENIX_PROJECT_NAME=knowledgeweaver
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_secret
```

## 📊 可观测性配置

### 1. CloudWatch 仪表板

自动创建的仪表板包括：
- **Application Metrics**: API请求量、延迟、错误率
- **Infrastructure Metrics**: CPU、内存、网络使用
- **Neo4j Metrics**: 查询性能、连接池状态
- **Cost Metrics**: 每日成本趋势

访问: AWS Console → CloudWatch → Dashboards → `knowledgeweaver-dashboard`

### 2. Phoenix 追踪

所有LLM调用和RAG检索会自动追踪：
```python
# 已集成在 backend/core/config.py
from phoenix.trace import trace

@trace()
async def extract_entities(text: str):
    # 自动记录输入、输出、延迟、成本
    ...
```

查看追踪: `http://<alb-dns>/phoenix`

### 3. 告警配置

Terraform 自动创建以下告警：
- ✅ API错误率 > 5%
- ✅ 响应时间 > 2s (P95)
- ✅ ECS CPU > 80%
- ✅ Neo4j 内存 > 85%
- ✅ 每日成本 > $5

SNS 主题: `knowledgeweaver-alerts` (需配置邮箱订阅)

## 🔐 安全配置

### 网络安全
- ✅ 应用运行在 Private Subnet
- ✅ 仅ALB暴露在Public Subnet
- ✅ Security Groups 最小权限原则
- ✅ Neo4j 不对外开放

### 密钥管理
```bash
# 所有敏感信息存储在 Secrets Manager
aws secretsmanager create-secret \
  --name knowledgeweaver/neo4j \
  --secret-string '{"username":"neo4j","password":"your-password"}'

aws secretsmanager create-secret \
  --name knowledgeweaver/langfuse \
  --secret-string '{"public_key":"pk_xxx","secret_key":"sk_xxx"}'
```

### IAM 权限
- ✅ ECS Task Role: 仅访问S3、Secrets Manager
- ✅ EC2 Instance Role: 仅访问CloudWatch、Systems Manager
- ✅ 启用 CloudTrail 审计所有API调用

## 🎯 面试演示要点

### 1. 架构设计决策 (5分钟)
展示架构图，解释：
- **为什么选择 Fargate**：无服务器，自动扩展，符合AI Ops自动化理念
- **为什么 Neo4j 用 EC2**：成本优化，AuraDB太贵
- **为什么 Private Subnet**：安全最佳实践，符合岗位安全要求

### 2. 可观测性实践 (5分钟)
打开 CloudWatch Dashboard + Phoenix，展示：
- **全链路追踪**：从API请求 → LLM调用 → 知识图谱检索
- **实时监控**：延迟、错误率、成本
- **告警机制**：演示告警配置和SNS通知

### 3. IaC 实践 (3分钟)
展示 Terraform 代码：
```bash
# 展示模块化设计
tree terraform/modules

# 展示变量管理
cat terraform/terraform.tfvars

# 展示状态管理
terraform state list
```

### 4. 成本优化 (2分钟)
展示 CloudWatch Cost Dashboard：
- **标签策略**：所有资源打上 `Project=KnowledgeWeaver`, `Environment=prod`
- **成本分解**：ECS、EC2、数据传输的成本占比
- **优化建议**：Spot Instance、Reserved Instance

## 📈 扩展功能（可选）

如果面试时间充裕，可以展示：

### 1. CI/CD 管道
```bash
# GitHub Actions 自动部署
.github/workflows/deploy.yml
```

### 2. 多环境管理
```bash
# dev / staging / prod
terraform workspace new prod
terraform workspace select prod
```

### 3. 灾难恢复
```bash
# 自动备份
aws backup create-backup-plan
```

### 4. Bedrock 集成
```python
# 替换 Claude CLI 为 AWS Bedrock
import boto3
bedrock = boto3.client('bedrock-runtime')
```

## 🔄 清理资源

面试完成后，删除所有资源避免费用：
```bash
cd terraform
terraform destroy --auto-approve
```

## 📚 相关文档

- [Terraform 配置详解](./TERRAFORM_GUIDE.md)
- [可观测性配置详解](./OBSERVABILITY_GUIDE.md)
- [成本优化最佳实践](./COST_OPTIMIZATION.md)

---

**预计部署时间**: 2-3天
**预计成本**: ~$100/月
**维护者**: Sheldon
**更新日期**: 2026-01-28
