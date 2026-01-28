# KnowledgeWeaver AWS EKS 部署指南

> **面向AI Ops Engineer面试的生产级Kubernetes部署方案**

## 🎯 架构概览

```
┌────────────────────────────────────────────────────────────┐
│                    AWS EKS Cluster                          │
│  (按需启动/停止 - Demo时开，平时关)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Kubernetes Namespace: prod              │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │   FastAPI   │  │   Neo4j     │  │   Phoenix   │ │  │
│  │  │ Deployment  │  │ StatefulSet │  │ Deployment  │ │  │
│  │  │ (2 replicas)│  │ (1 replica) │  │ (1 replica) │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  │         ↑                ↑                ↑          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │  Langfuse   │  │ PostgreSQL  │  │   Services  │ │  │
│  │  │ Deployment  │  │ StatefulSet │  │ (ClusterIP) │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  │         ↑                                            │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │    Ingress (AWS ALB Controller)             │   │  │
│  │  │    → ALB (Application Load Balancer)        │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  EBS Volumes    │  │  ECR Registry   │                 │
│  │  (Persistent)   │  │  (Docker Images)│                 │
│  └─────────────────┘  └─────────────────┘                 │
└────────────────────────────────────────────────────────────┘
         ↓                           ↓
  CloudWatch Logs              S3 Bucket
```

## 📦 项目结构

```
deploy/
├── docker/                       # Docker配置
│   ├── api/
│   │   ├── Dockerfile           # FastAPI应用镜像
│   │   └── .dockerignore
│   └── docker-compose.yml       # 本地测试环境
│
├── kubernetes/                   # Kubernetes配置
│   ├── base/
│   │   ├── namespace.yaml       # prod命名空间
│   │   ├── configmap.yaml       # 应用配置
│   │   ├── secrets.yaml         # 密钥配置（模板）
│   │   ├── ingress.yaml         # ALB入口
│   │   │
│   │   ├── api/                 # FastAPI服务
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── hpa.yaml         # 自动扩展
│   │   │
│   │   ├── neo4j/               # 图数据库
│   │   │   ├── statefulset.yaml
│   │   │   └── service.yaml
│   │   │
│   │   └── observability/       # 可观测性
│   │       ├── phoenix/
│   │       ├── langfuse/
│   │       └── postgres/
│   │
│   └── scripts/
│       ├── start-cluster.sh     # 启动集群
│       ├── stop-cluster.sh      # 停止集群
│       ├── status.sh            # 查看状态
│       ├── deploy.sh            # 部署应用
│       └── install-alb-controller.sh
│
└── terraform/                    # Infrastructure as Code
    ├── main.tf                  # 主配置
    ├── variables.tf             # 变量定义
    ├── outputs.tf               # 输出值
    ├── backend.tf               # State管理
    ├── terraform.tfvars.example # 配置模板
    │
    ├── modules/
    │   ├── vpc/                 # VPC网络
    │   ├── eks/                 # EKS集群
    │   ├── ecr/                 # 镜像仓库
    │   ├── s3/                  # 对象存储
    │   ├── cloudwatch/          # 监控告警
    │   └── iam/                 # 权限管理
    │
    └── scripts/
        ├── init.sh              # 初始化Terraform
        ├── apply.sh             # 创建基础设施
        └── destroy.sh           # 销毁基础设施
```

## 🚀 快速开始

### 前置要求

1. **AWS CLI** 已安装并配置
   ```bash
   aws --version
   aws configure
   ```

2. **Terraform** >= 1.0
   ```bash
   terraform --version
   ```

3. **kubectl** >= 1.28
   ```bash
   kubectl version --client
   ```

4. **Helm** >= 3.0
   ```bash
   helm version
   ```

5. **Docker** 已安装
   ```bash
   docker --version
   ```

### 步骤1：创建AWS基础设施（15-20分钟）

```bash
cd deploy/terraform

# 1. 复制配置文件
cp terraform.tfvars.example terraform.tfvars

# 2. 编辑配置（必须修改owner）
vim terraform.tfvars

# 3. 初始化Terraform
./scripts/init.sh

# 4. 预览将要创建的资源
terraform plan

# 5. 创建基础设施（15-20分钟）
./scripts/apply.sh
```

**创建的资源：**
- ✅ VPC + Subnets + NAT Gateways
- ✅ EKS Cluster（Kubernetes 1.28）
- ✅ EKS Node Group（2x t3.medium）
- ✅ ECR Repository
- ✅ S3 Bucket
- ✅ CloudWatch Logs
- ✅ IAM Roles & Policies

### 步骤2：配置kubectl

```bash
# Terraform输出包含配置命令
terraform output configure_kubectl

# 执行命令（示例）
aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production

# 验证连接
kubectl get nodes
```

### 步骤3：安装AWS Load Balancer Controller

```bash
cd ../kubernetes/scripts

# 安装ALB Controller（需要Helm）
./install-alb-controller.sh

# 验证安装
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### 步骤4：构建并推送Docker镜像

```bash
cd ../../..  # 回到项目根目录

# 1. 获取ECR仓库URL
export ECR_REPO=$(cd deploy/terraform && terraform output -json ecr_repository_urls | jq -r '.["knowledgeweaver-api"]')
echo $ECR_REPO

# 2. 登录ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin $(echo $ECR_REPO | cut -d'/' -f1)

# 3. 构建镜像
docker build -t $ECR_REPO:latest -f deploy/docker/api/Dockerfile .

# 4. 推送镜像
docker push $ECR_REPO:latest
```

### 步骤5：更新Kubernetes配置并部署

```bash
cd deploy/kubernetes

# 1. 更新deployment.yaml中的镜像地址
export ECR_REPO=$(cd ../terraform && terraform output -json ecr_repository_urls | jq -r '.["knowledgeweaver-api"]')
sed -i.bak "s|PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest|$ECR_REPO:latest|g" base/api/deployment.yaml

# 2. 配置Secrets（必须修改密码！）
vim base/secrets.yaml  # 修改所有密码

# 3. 部署应用
./scripts/deploy.sh

# 4. 等待所有Pod就绪
kubectl wait --for=condition=Ready pods --all -n prod --timeout=300s
```

### 步骤6：获取访问地址

```bash
# 获取ALB URL（需等待2-3分钟）
kubectl get ingress knowledgeweaver-ingress -n prod

# 输出示例：
# NAME                        CLASS   HOSTS   ADDRESS                                    PORTS   AGE
# knowledgeweaver-ingress     alb     *       k8s-prod-xxx.ap-southeast-2.elb.amazonaws.com   80      5m

# 访问应用
export ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "🌐 Main App:    http://$ALB_URL"
echo "📖 API Docs:    http://$ALB_URL/docs"
echo "🔍 Phoenix:     http://$ALB_URL/phoenix"
echo "📈 Langfuse:    http://$ALB_URL/langfuse"
```

## 💰 成本优化：按需启停

### 核心思路："用时开，不用关"

EKS集群可以缩容到0节点，只保留控制平面，大幅节省成本。

### 停止集群（节省$0.16/小时）

```bash
cd deploy/kubernetes/scripts
./stop-cluster.sh
```

**效果：**
- ✅ Worker节点缩容到0
- ✅ 数据保留在EBS卷中（Neo4j、Phoenix）
- ✅ 控制平面继续运行（$73/月）
- 💰 **节省约$115/月**

### 启动集群（5分钟）

```bash
./start-cluster.sh
```

**效果：**
- ✅ Worker节点从0扩展到2
- ✅ 所有Pod自动启动
- ✅ 数据完整恢复
- ⏱️ **总耗时约5分钟**

### 查看状态

```bash
./status.sh
```

### 成本对比

| 场景 | 配置 | 月成本 |
|------|------|--------|
| **24x7运行** | 控制平面 + 2节点 + NAT | ~$228 ❌ |
| **按需使用（推荐）** | 控制平面 + 节点按需 | ~$100 ✅ |
| **仅Demo用** | 每次Demo开3小时，月2次 | ~$74 ⭐ |

**Demo场景成本：**
- EKS控制平面：$73/月（固定）
- Worker节点：$0.08/h × 2节点 × 6h/月 = $0.96
- **总计：~$74/月**

## 🔍 监控和可观测性

### Phoenix（实时追踪）

访问：`http://<ALB_URL>/phoenix`

**功能：**
- ✅ LLM调用全链路追踪
- ✅ Token和成本追踪
- ✅ 性能分析（哪个环节最慢）
- ✅ 错误诊断

### Langfuse（深度分析）

访问：`http://<ALB_URL>/langfuse`

**功能：**
- ✅ 多轮对话追踪
- ✅ Prompt版本管理
- ✅ 成本分析和优化建议
- ✅ 质量评估（Hallucination检测）

### CloudWatch（基础设施监控）

```bash
# 查看Pod日志
kubectl logs -f deployment/api -n prod

# 查看事件
kubectl get events -n prod --sort-by='.lastTimestamp'

# CloudWatch Logs Insights查询
aws logs tail /aws/eks/knowledgeweaver-production/application --follow
```

### 查看监控指标

```bash
# Pod资源使用
kubectl top pods -n prod

# 节点资源使用
kubectl top nodes

# HPA状态
kubectl get hpa -n prod
```

## 🛠️ 常用运维命令

### 应用更新

```bash
# 1. 构建新镜像
docker build -t $ECR_REPO:v2.0 -f deploy/docker/api/Dockerfile .
docker push $ECR_REPO:v2.0

# 2. 更新部署
kubectl set image deployment/api api=$ECR_REPO:v2.0 -n prod

# 3. 查看滚动更新状态
kubectl rollout status deployment/api -n prod

# 4. 回滚（如果有问题）
kubectl rollout undo deployment/api -n prod
```

### 扩缩容

```bash
# 手动扩展Pod数量
kubectl scale deployment/api --replicas=3 -n prod

# 查看HPA自动扩展
kubectl get hpa -n prod -w
```

### 调试

```bash
# 进入Pod
kubectl exec -it deployment/api -n prod -- /bin/bash

# 查看Pod详情
kubectl describe pod <pod-name> -n prod

# 查看服务端点
kubectl get endpoints -n prod

# 测试服务连接
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n prod -- \
  curl http://api:9621/health
```

### 数据备份

```bash
# Neo4j数据导出
kubectl exec -it neo4j-0 -n prod -- neo4j-admin dump --to=/tmp/backup.dump
kubectl cp prod/neo4j-0:/tmp/backup.dump ./neo4j-backup.dump

# PostgreSQL备份
kubectl exec -it postgres-0 -n prod -- pg_dump -U langfuse langfuse > langfuse-backup.sql
```

## 🎯 面试演示要点（15-20分钟）

### 1. 开场：一键启动（2分钟）

```bash
# 展示当前状态
./scripts/status.sh
# → 显示：2个节点运行

# 访问应用
open http://<ALB_URL>
```

**说明：**
> "这是一个按需启动的EKS集群，平时可以缩容到0节点节省成本，Demo时5分钟启动。"

### 2. Kubernetes架构（5分钟）

```bash
# 展示所有资源
kubectl get all -n prod

# 展示StatefulSet（持久化）
kubectl describe statefulset neo4j -n prod

# 展示Ingress（ALB）
kubectl describe ingress knowledgeweaver-ingress -n prod
```

**关键点：**
- StatefulSet vs Deployment
- EBS持久化卷
- 服务发现（neo4j:7687）
- ALB自动创建和健康检查

### 3. 可观测性全链路（5分钟）⭐

```bash
# 1. 打开Phoenix
open http://<ALB_URL>/phoenix

# 2. 发起测试请求
curl -X POST http://<ALB_URL>/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "定投是什么？", "mode": "hybrid"}'

# 3. 在Phoenix中查看追踪链
```

**演示内容：**
- 全链路追踪（向量检索 → 图查询 → LLM）
- Token和成本追踪
- 性能分析
- Langfuse深度分析

### 4. IaC + GitOps（3分钟）

```bash
# 展示Terraform模块
tree deploy/terraform/modules

# 展示一键创建
terraform plan  # 显示将创建的资源
```

**说明：**
> "使用Terraform模块化管理基础设施，版本控制，可重复部署。"

### 5. 成本优化（2分钟）

```bash
# 展示成本策略
./scripts/status.sh  # 显示当前成本

# 演示停止（可选）
./scripts/stop-cluster.sh
```

**关键指标：**
- 平时节点=0，成本$73/月
- Demo时按需开启
- CloudWatch成本监控

### 6. 收尾：技术总结（2分钟）

**展示的核心能力：**
1. ✅ **Kubernetes运维**：EKS集群、服务编排、StatefulSet、HPA
2. ✅ **可观测性**：Phoenix全链路追踪、Langfuse分析、CloudWatch监控
3. ✅ **IaC**：Terraform模块化、版本化管理
4. ✅ **FinOps**：按需启停，成本优化
5. ✅ **安全**：IRSA、Secrets Manager、网络隔离

## 🔒 安全最佳实践

### 1. Secrets管理

```bash
# 生产环境：使用AWS Secrets Manager
kubectl create secret generic knowledgeweaver-secrets \
  --from-literal=neo4j-password=$(aws secretsmanager get-secret-value \
    --secret-id prod/knowledgeweaver/neo4j --query SecretString --output text) \
  -n prod
```

### 2. 网络隔离

- ✅ Worker节点在私有子网
- ✅ 通过NAT Gateway访问互联网
- ✅ Security Group限制入站流量
- ✅ Network Policy隔离Pod

### 3. IAM最小权限（IRSA）

```bash
# Pod使用IAM Role访问AWS服务
kubectl annotate serviceaccount knowledgeweaver-sa \
  eks.amazonaws.com/role-arn=arn:aws:iam::123456:role/pod-execution-role \
  -n prod
```

### 4. 镜像扫描

```bash
# ECR自动扫描
aws ecr describe-image-scan-findings \
  --repository-name knowledgeweaver-production-knowledgeweaver-api \
  --image-id imageTag=latest
```

## 🗑️ 清理资源

### 删除应用（保留基础设施）

```bash
cd deploy/kubernetes/scripts
kubectl delete namespace prod
```

### 完全删除（包括基础设施）

```bash
cd deploy/terraform
./scripts/destroy.sh

# ⚠️  警告：这将删除所有资源，包括数据！
```

## 📚 参考文档

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

## 🆘 故障排查

### Pod无法启动

```bash
# 查看Pod状态
kubectl describe pod <pod-name> -n prod

# 查看日志
kubectl logs <pod-name> -n prod --previous

# 查看事件
kubectl get events -n prod --sort-by='.lastTimestamp'
```

### ALB无法访问

```bash
# 检查Ingress状态
kubectl describe ingress knowledgeweaver-ingress -n prod

# 检查ALB Controller日志
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# 检查安全组规则
aws ec2 describe-security-groups --filters "Name=tag:kubernetes.io/cluster/knowledgeweaver-production,Values=owned"
```

### Neo4j数据丢失

```bash
# 检查PVC
kubectl get pvc -n prod

# 检查PV
kubectl get pv

# 查看StatefulSet
kubectl describe statefulset neo4j -n prod
```

---

**版本：** 1.0.0
**更新日期：** 2026-01-28
**维护者：** Sheldon
