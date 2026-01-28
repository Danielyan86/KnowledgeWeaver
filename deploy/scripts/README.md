# KnowledgeWeaver All-in-One Scripts

> **一键启动/停止整个AWS EKS部署**

## 🚀 快速开始

### 1. 启动所有服务（第一次部署）

```bash
cd deploy/scripts
./start-all.sh
```

**这会自动：**
1. ✅ 创建AWS基础设施（VPC, EKS, ECR, S3...）- 如果不存在
2. ✅ 或启动已停止的EKS节点 - 如果基础设施已存在
3. ✅ 配置kubectl
4. ✅ 安装AWS Load Balancer Controller
5. ✅ 构建并推送Docker镜像
6. ✅ 部署Kubernetes应用
7. ✅ 获取访问URL

**预计时间：**
- 第一次：15-20分钟（创建基础设施）
- 后续启动：5-10分钟（只启动节点）

### 2. 查看状态

```bash
./status-all.sh
```

**显示：**
- CloudFormation Stack状态
- EKS Cluster状态
- Worker节点数量
- Kubernetes Pods状态
- ALB访问地址
- 当前成本估算

### 3. 停止所有服务

```bash
./stop-all.sh
```

**两种模式：**

#### 模式1：快速停止（推荐）⭐
- 停止EKS worker节点（缩容到0）
- 保留基础设施（VPC, EKS控制平面等）
- 数据保留在EBS卷中
- 快速重启（~5分钟）
- 成本：~$73/月（仅控制平面）

#### 模式2：完全删除
- 删除所有AWS资源
- 所有数据丢失
- 月成本：$0
- 重新部署需要15-20分钟

## 📋 脚本说明

### start-all.sh
**功能：**
- 智能检测当前状态
- 自动创建或启动基础设施
- 部署所有应用
- 提供访问URL

**使用场景：**
- 第一次部署
- 从停止状态恢复
- 重新部署应用

### stop-all.sh
**功能：**
- 交互式选择停止模式
- 快速停止或完全删除
- 显示成本影响

**使用场景：**
- Demo结束后节省成本
- 长期不用时完全清理
- 测试完成后清理

### status-all.sh
**功能：**
- 显示所有组件状态
- 实时成本估算
- 快速诊断问题

**使用场景：**
- 检查部署状态
- 监控成本
- 排查问题

## 🎯 典型使用流程

### 场景1：第一次部署
```bash
# 1. 启动所有服务
./start-all.sh
# 等待15-20分钟

# 2. 查看状态
./status-all.sh

# 3. 访问应用
open http://<ALB_URL>

# 4. Demo完成后停止（节省成本）
./stop-all.sh
# 选择 "1) Quick Stop"
```

### 场景2：已部署，从停止状态恢复
```bash
# 1. 启动服务（5-10分钟）
./start-all.sh

# 2. 访问应用
./status-all.sh  # 获取ALB URL
```

### 场景3：完全清理
```bash
# 删除所有资源
./stop-all.sh
# 选择 "2) Full Destroy"
# 输入 "DELETE EVERYTHING"
```

## 💰 成本对比

| 状态 | 配置 | 月成本 | 说明 |
|------|------|--------|------|
| **运行中** | 控制平面 + 2节点 + NAT | ~$228 | 24x7运行 |
| **停止** | 控制平面 | ~$73 | 快速恢复 |
| **删除** | 无 | $0 | 需重新部署 |

### 推荐策略

#### Demo/面试场景：
- 面试前：`./start-all.sh` (10分钟前)
- 面试后：`./stop-all.sh` → 选择1
- 月成本：~$74（EKS控制平面）

#### 开发测试：
- 工作时：`./start-all.sh`
- 下班后：`./stop-all.sh` → 选择1
- 周末/假期：`./stop-all.sh` → 选择2
- 平均月成本：~$100

#### 长期不用：
- `./stop-all.sh` → 选择2（完全删除）
- 成本：$0

## 🔍 故障排查

### 问题1：start-all.sh失败
```bash
# 检查AWS凭证
aws sts get-caller-identity

# 检查CloudFormation状态
cd ../cloudformation/scripts
./status.sh

# 查看详细日志
kubectl get events -n prod --sort-by='.lastTimestamp'
```

### 问题2：无法访问集群
```bash
# 重新配置kubectl
aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production

# 验证连接
kubectl get nodes
```

### 问题3：ALB URL不可用
```bash
# 检查Ingress状态
kubectl describe ingress knowledgeweaver-ingress -n prod

# 检查ALB Controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller
```

## 📝 注意事项

### 环境变量
脚本会自动设置：
- `AWS_PROFILE=sheldon2026`
- `AWS_REGION=ap-southeast-2`

如需修改，编辑脚本开头的变量。

### 数据持久化
**快速停止模式（模式1）：**
- ✅ Neo4j数据保留（EBS卷）
- ✅ Phoenix数据保留（EBS卷）
- ✅ PostgreSQL数据保留（EBS卷）

**完全删除模式（模式2）：**
- ❌ 所有数据丢失
- ❌ 需要重新导入数据

### 首次运行检查
```bash
# 确保AWS CLI已配置
aws configure list

# 确保kubectl已安装
kubectl version --client

# 确保Docker已运行
docker ps
```

## 🚀 进阶用法

### 只重新部署应用（不重建基础设施）
```bash
./start-all.sh
# 当询问"Redeploy applications?"时选择 y
```

### 只重建Docker镜像
```bash
./start-all.sh
# 当询问"Rebuild?"时选择 y
```

### 自定义参数
编辑`../cloudformation/parameters.json`修改：
- 节点类型（默认：t3.medium）
- 节点数量（默认：2）
- Kubernetes版本（默认：1.28）

然后重新运行：
```bash
cd ../cloudformation/scripts
./deploy.sh  # CloudFormation会自动更新
```

## 📚 相关文档

- [AWS EKS部署指南](../../docs/AWS_EKS_DEPLOYMENT.md)
- [CloudFormation README](../cloudformation/README.md)
- [部署总结](../DEPLOYMENT_SUMMARY.md)

---

**版本：** 1.0.0
**更新日期：** 2026-01-28
