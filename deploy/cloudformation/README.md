# KnowledgeWeaver AWS CloudFormation 部署

> **使用AWS原生工具（CloudFormation）部署整个基础设施**

## 📦 包含的资源

CloudFormation会自动创建以下所有AWS资源：

### 网络层
- ✅ VPC (10.0.0.0/16)
- ✅ 2个公有子网（用于ALB和NAT）
- ✅ 2个私有子网（用于EKS Worker节点）
- ✅ Internet Gateway
- ✅ 2个NAT Gateways（高可用）
- ✅ 路由表配置

### 计算层
- ✅ EKS Cluster (Kubernetes 1.28)
- ✅ EKS Managed Node Group (2x t3.medium)
- ✅ EKS Addons (EBS CSI, VPC CNI, CoreDNS, kube-proxy)
- ✅ IAM Roles & Policies

### 存储层
- ✅ ECR Repository（Docker镜像）
- ✅ S3 Bucket（文档存储）
- ✅ 自动生命周期管理

### 监控层
- ✅ CloudWatch Log Groups
- ✅ CloudWatch Dashboard
- ✅ Cost Alarms
- ✅ SNS Topic（告警通知）

## 🚀 快速开始

### 前置要求

1. **AWS CLI** 已配置
   ```bash
   aws configure
   # 输入 AWS Access Key ID
   # 输入 AWS Secret Access Key
   # Region: ap-southeast-2 (Sydney)
   ```

2. **kubectl** 已安装
   ```bash
   kubectl version --client
   ```

3. **Docker** 已安装
   ```bash
   docker --version
   ```

### 步骤1：部署基础设施（一键部署）

```bash
cd deploy/cloudformation/scripts

# 执行部署脚本
./deploy.sh
```

**这会自动：**
1. ✅ 验证CloudFormation模板
2. ✅ 创建主Stack和所有嵌套Stacks
3. ✅ 等待所有资源创建完成（15-20分钟）
4. ✅ 输出所有访问信息

### 步骤2：配置kubectl

```bash
# 获取配置命令（从输出中）
aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production

# 验证连接
kubectl get nodes
```

### 步骤3：安装AWS Load Balancer Controller

```bash
cd ../../kubernetes/scripts
./install-alb-controller.sh
```

### 步骤4：构建并推送Docker镜像

```bash
# 回到项目根目录
cd ../../..

# 获取ECR仓库URL（从CloudFormation输出）
export ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
  --output text)

echo $ECR_REPO

# 登录ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin $(echo $ECR_REPO | cut -d'/' -f1)

# 构建镜像
docker build -t $ECR_REPO:latest -f deploy/docker/api/Dockerfile .

# 推送镜像
docker push $ECR_REPO:latest
```

### 步骤5：部署应用到Kubernetes

```bash
cd deploy/kubernetes

# 更新deployment.yaml中的镜像地址
export ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
  --output text)

sed -i.bak "s|PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest|$ECR_REPO:latest|g" base/api/deployment.yaml

# 配置Secrets
vim base/secrets.yaml  # 修改所有密码

# 部署
./scripts/deploy.sh

# 等待Pod就绪
kubectl wait --for=condition=Ready pods --all -n prod --timeout=300s
```

### 步骤6：获取访问地址

```bash
# 获取ALB URL
kubectl get ingress knowledgeweaver-ingress -n prod

# 访问应用
export ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "🌐 Main App:    http://$ALB_URL"
echo "📖 API Docs:    http://$ALB_URL/docs"
echo "🔍 Phoenix:     http://$ALB_URL/phoenix"
echo "📈 Langfuse:    http://$ALB_URL/langfuse"
```

## 📊 查看状态

```bash
cd deploy/cloudformation/scripts

# 查看所有Stack状态
./status.sh
```

## 💰 成本优化：按需启停

CloudFormation创建的EKS集群支持节点缩容，节省成本。

### 停止集群（节省成本）

```bash
cd ../../kubernetes/scripts
./stop-cluster.sh
```

### 启动集群

```bash
./start-cluster.sh
```

## 🔄 更新基础设施

修改`parameters.json`后重新部署：

```bash
cd deploy/cloudformation/scripts
./deploy.sh  # CloudFormation会自动检测变更并更新
```

## 🗑️ 完全删除

```bash
cd deploy/cloudformation/scripts
./destroy.sh

# ⚠️  警告：会删除所有资源和数据！
```

## 📁 文件结构

```
cloudformation/
├── templates/
│   ├── main.yaml          # 主模板（orchestrator）
│   ├── vpc.yaml           # VPC和网络
│   ├── eks.yaml           # EKS集群和节点组
│   ├── ecr.yaml           # Docker镜像仓库
│   ├── s3.yaml            # 文档存储
│   └── cloudwatch.yaml    # 监控和告警
│
├── parameters.json        # 配置参数
├── outputs.json           # 部署后的输出（自动生成）
│
└── scripts/
    ├── deploy.sh          # 部署脚本
    ├── destroy.sh         # 删除脚本
    └── status.sh          # 状态查询
```

## 🔍 CloudFormation vs Terraform

| 特性 | CloudFormation | Terraform |
|------|----------------|-----------|
| **提供商** | AWS原生 | 第三方（HashiCorp） |
| **工具** | AWS CLI（内置） | 需安装terraform CLI |
| **多云支持** | ❌ AWS专用 | ✅ AWS/GCP/Azure |
| **AWS集成** | ✅ 原生深度集成 | ⚠️ 需配置 |
| **语法** | YAML/JSON | HCL |
| **状态管理** | AWS托管（自动） | 需配置S3后端 |
| **回滚** | ✅ 自动 | ⚠️ 手动 |

**我们选择CloudFormation**因为：
1. ✅ AWS原生，无需额外工具
2. ✅ 自动状态管理
3. ✅ 展示AWS专业度（面试加分）

## 📚 参考文档

- [AWS CloudFormation官方文档](https://docs.aws.amazon.com/cloudformation/)
- [EKS CloudFormation资源](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_EKS.html)
- [CloudFormation最佳实践](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)

## 🆘 故障排查

### Stack创建失败

```bash
# 查看失败原因
aws cloudformation describe-stack-events \
  --stack-name knowledgeweaver-production \
  --max-items 20

# CloudFormation会自动回滚
```

### 手动回滚

```bash
# 删除失败的Stack
aws cloudformation delete-stack --stack-name knowledgeweaver-production

# 重新部署
./deploy.sh
```

---

**版本：** 1.0.0
**更新日期：** 2026-01-28
