# 公网访问配置指南

## 快速开始（推荐方式 2）

### 步骤 1: 部署 LoadBalancer Service

```bash
# 应用 LoadBalancer 配置
kubectl apply -f deploy/kubernetes/base/api/service-loadbalancer.yaml
```

### 步骤 2: 等待 AWS 创建 Load Balancer

```bash
# 监控创建进度（约 2-3 分钟）
kubectl get svc api-public -n demo --watch

# 看到 EXTERNAL-IP 从 <pending> 变为 DNS 名称即可
# NAME         TYPE           EXTERNAL-IP
# api-public   LoadBalancer   a1b2c3.ap-southeast-2.elb.amazonaws.com
```

### 步骤 3: 获取公网地址

```bash
# 获取 Load Balancer URL
LB_URL=$(kubectl get svc api-public -n demo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "API URL: http://${LB_URL}"
```

### 步骤 4: 测试访问

```bash
# 健康检查
curl http://${LB_URL}/health

# API 文档
curl http://${LB_URL}/docs

# 在浏览器中访问
open http://${LB_URL}/docs
```

---

## 三种访问方式详解

### 方式 1: AWS Application Load Balancer (ALB)

**适合：生产环境，需要高级路由功能**

#### 安装 AWS Load Balancer Controller

```bash
# 运行安装脚本
./deploy/kubernetes/scripts/install-alb-controller.sh
```

#### 部署 Ingress

```bash
kubectl apply -f deploy/kubernetes/base/ingress.yaml
```

#### 获取 ALB 地址

```bash
kubectl get ingress -n demo

# 输出：
# NAME                       ADDRESS
# knowledgeweaver-ingress    k8s-demo-knowledge-xxx.elb.amazonaws.com

# 访问 API
curl http://k8s-demo-knowledge-xxx.elb.amazonaws.com/health
```

#### 路由规则

```
http://ALB_URL/api       → API 服务
http://ALB_URL/health    → 健康检查
http://ALB_URL/docs      → API 文档
http://ALB_URL/phoenix   → Phoenix 监控
http://ALB_URL/langfuse  → Langfuse 监控
http://ALB_URL/          → 前端页面
```

---

### 方式 2: Network Load Balancer (NLB) - 推荐演示

**适合：演示、测试、简单部署**

#### 部署

```bash
kubectl apply -f deploy/kubernetes/base/api/service-loadbalancer.yaml
```

#### 获取地址

```bash
kubectl get svc api-public -n demo

# 输出：
# NAME         TYPE           EXTERNAL-IP                                PORT(S)
# api-public   LoadBalancer   a1b2c3.ap-southeast-2.elb.amazonaws.com   80:31234/TCP
```

#### 访问

```bash
# 通过 NLB（端口 80）
curl http://a1b2c3.ap-southeast-2.elb.amazonaws.com/health

# 浏览器访问
open http://a1b2c3.ap-southeast-2.elb.amazonaws.com/docs
```

#### 成本估算

- NLB 小时费用: ~$0.0225/hour (~$16/月)
- 数据传输: 按量计费
- **演示用途：约 $20-30/月**

---

### 方式 3: NodePort

**适合：快速测试、开发环境**

#### 部署

```bash
kubectl apply -f deploy/kubernetes/base/api/service-nodeport.yaml
```

#### 获取 Node IP

```bash
# 方式 1: kubectl
kubectl get nodes -o wide

# 方式 2: AWS CLI
aws ec2 describe-instances \
  --filters "Name=tag:eks:cluster-name,Values=knowledgeweaver-production" \
  --query "Reservations[].Instances[].PublicIpAddress" \
  --output text
```

#### 配置 Security Group

需要在 Node 的 Security Group 中添加入站规则：

```bash
# 获取 Node Security Group ID
NODE_SG=$(aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=*node*" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

# 添加入站规则（允许端口 30621）
aws ec2 authorize-security-group-ingress \
  --group-id ${NODE_SG} \
  --protocol tcp \
  --port 30621 \
  --cidr 0.0.0.0/0
```

#### 访问

```bash
# 使用 Node IP + NodePort
NODE_IP=13.239.123.45  # 替换为实际 Node IP
curl http://${NODE_IP}:30621/health
```

---

## 故障排查

### LoadBalancer Pending 不变

```bash
# 检查 Service 状态
kubectl describe svc api-public -n demo

# 常见原因：
# 1. 子网没有标签 (kubernetes.io/role/elb = 1)
# 2. Node 没有正确的 IAM 权限
# 3. VPC 配置问题
```

### 无法访问 NodePort

```bash
# 1. 检查 Pod 状态
kubectl get pods -n demo

# 2. 检查 Service
kubectl get svc -n demo

# 3. 检查 Security Group
aws ec2 describe-security-groups --group-ids ${NODE_SG}

# 4. 测试从 Pod 内部访问
kubectl exec -it <pod-name> -n demo -- curl localhost:9621/health
```

### ALB 创建失败

```bash
# 查看 ALB Controller 日志
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# 常见问题：
# 1. OIDC Provider 未配置
# 2. IAM 权限不足
# 3. 子网标签缺失
```

---

## 清理资源

### 删除 LoadBalancer

```bash
kubectl delete -f deploy/kubernetes/base/api/service-loadbalancer.yaml

# AWS 会自动删除 NLB（约 1-2 分钟）
```

### 删除 Ingress

```bash
kubectl delete -f deploy/kubernetes/base/ingress.yaml

# AWS 会自动删除 ALB
```

### 删除 NodePort Security Group 规则

```bash
aws ec2 revoke-security-group-ingress \
  --group-id ${NODE_SG} \
  --protocol tcp \
  --port 30621 \
  --cidr 0.0.0.0/0
```

---

## 最佳实践

### 演示环境

```bash
# 推荐：使用 LoadBalancer
✅ 简单快速
✅ 稳定可靠
✅ 成本可控（~$20-30/月）
```

### 生产环境

```bash
# 推荐：使用 Ingress + ALB
✅ 高级路由
✅ SSL/TLS 支持
✅ WAF 集成
✅ 成本优化（一个 ALB 服务多个应用）
```

### 测试环境

```bash
# 推荐：使用 NodePort 或 Port Forward
✅ 零成本
✅ 快速验证
❌ 不适合长期使用
```

---

## 快速命令参考

```bash
# 获取 LoadBalancer URL
kubectl get svc api-public -n demo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# 获取 Ingress URL
kubectl get ingress -n demo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# 获取 Node IP
kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}'

# 测试健康检查
curl http://<URL>/health

# 打开 API 文档
open http://<URL>/docs
```

---

**更新日期**: 2026-01-29
**维护者**: Sheldon
