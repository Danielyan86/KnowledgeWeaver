# AWS EKS 核心概念详解

## 目录
- [概述](#概述)
- [1. EKS Cluster（EKS 集群）](#1-eks-cluster-eks-集群)
- [2. Node Group（节点组）](#2-node-group-节点组)
- [3. CoreDNS Addon（DNS 服务）](#3-coredns-addon-dns-服务)
- [4. Kube Proxy Addon（网络代理）](#4-kube-proxy-addon-网络代理)
- [5. VPC CNI Addon（容器网络接口）](#5-vpc-cni-addon-容器网络接口)
- [6. EBS CSI Driver Addon（存储驱动）](#6-ebs-csi-driver-addon-存储驱动)
- [组件依赖关系](#组件依赖关系)
- [在 KnowledgeWeaver 中的应用](#在-knowledgeweaver-中的应用)

---

## 概述

AWS EKS (Elastic Kubernetes Service) 是 AWS 提供的托管 Kubernetes 服务。部署一个完整的 EKS 集群需要多个核心组件协同工作，这些组件按照特定顺序安装，确保集群能够正常运行。

**部署顺序：**
```
1. EKS Cluster (集群控制平面)
   ↓
2. Node Group (工作节点)
   ↓
3. 核心插件并行安装：
   ├── CoreDNS (DNS 解析)
   ├── Kube Proxy (网络代理)
   ├── VPC CNI (容器网络)
   └── EBS CSI Driver (持久化存储)
```

---

## 1. EKS Cluster (EKS 集群)

### 是什么？
EKS Cluster 是 Kubernetes 的**控制平面**（Control Plane），负责管理整个 Kubernetes 集群的大脑。

### 核心功能
- **API Server**：所有操作的入口（kubectl 命令通过这里执行）
- **Scheduler**：决定 Pod 运行在哪个节点
- **Controller Manager**：维护集群期望状态（如副本数、健康检查）
- **etcd**：存储集群所有配置和状态数据

### AWS 托管的优势
- AWS 自动管理控制平面的高可用（多个可用区）
- 自动升级和打补丁
- 与 AWS IAM、VPC、CloudWatch 深度集成

### 在 KnowledgeWeaver 中
```yaml
# 控制平面配置示例
cluster_name: knowledgeweaver-cluster
version: 1.28
region: us-west-2

# 控制平面访问端点
endpoint: https://ABC123.gr7.us-west-2.eks.amazonaws.com
```

**作用：**
- 接收 `kubectl apply` 命令（部署 Neo4j、API 服务等）
- 调度 Pod 到合适的节点
- 监控服务健康状态

---

## 2. Node Group (节点组)

### 是什么？
Node Group 是一组 **EC2 实例**，作为 Kubernetes 的**工作节点**（Worker Nodes），实际运行应用容器。

### 核心功能
- **运行 Pod**：所有容器化应用运行在这些节点上
- **资源提供**：提供 CPU、内存、存储、网络资源
- **自动伸缩**：根据负载自动增减节点数量

### 节点类型选择
```bash
# 通用型（推荐开发环境）
instance_type: t3.medium
  - CPU: 2 vCPU
  - 内存: 4 GB
  - 适用: API 服务、小规模 Neo4j

# 内存优化型（生产环境）
instance_type: r5.large
  - CPU: 2 vCPU
  - 内存: 16 GB
  - 适用: Neo4j 数据库、大规模图谱

# 计算优化型（AI 推理）
instance_type: c5.xlarge
  - CPU: 4 vCPU
  - 内存: 8 GB
  - 适用: 高并发 API、向量计算
```

### 在 KnowledgeWeaver 中
```hcl
# Terraform 配置
node_group_name = "knowledgeweaver-nodes"
instance_types  = ["t3.medium"]
desired_size    = 2  # 正常运行 2 个节点
min_size        = 1  # 最少 1 个节点
max_size        = 4  # 最多扩展到 4 个节点
```

**作用：**
- 节点 1：运行 Neo4j 数据库 + API 服务
- 节点 2：运行 API 服务（高可用）
- 自动扩展：流量增加时自动添加节点

---

## 3. CoreDNS Addon (DNS 服务)

### 是什么？
CoreDNS 是 Kubernetes 集群内部的 **DNS 解析服务**，让 Pod 之间可以通过服务名互相访问。

### 核心功能
- **服务发现**：通过服务名解析到 Pod IP
- **负载均衡**：自动轮询多个 Pod 实例
- **外部 DNS**：支持解析集群外部域名

### 工作原理
```
# 场景：API Pod 访问 Neo4j 服务

1. API Pod 发起请求：
   http://neo4j-service:7474

2. CoreDNS 解析：
   neo4j-service → 10.100.1.50 (Service ClusterIP)

3. Service 转发到 Pod：
   10.100.1.50 → 10.244.1.10 (Neo4j Pod IP)

4. 请求到达 Neo4j
```

### 在 KnowledgeWeaver 中
```yaml
# API 服务访问 Neo4j（无需知道 IP）
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  NEO4J_URI: "bolt://neo4j-service:7687"  # 服务名，CoreDNS 自动解析
```

**作用：**
- API 通过 `neo4j-service` 访问数据库，无需硬编码 IP
- Neo4j 重启后 IP 变化，服务名不变
- 支持跨命名空间访问：`neo4j-service.production.svc.cluster.local`

---

## 4. Kube Proxy Addon (网络代理)

### 是什么？
Kube Proxy 运行在**每个节点**上，负责实现 Kubernetes **Service 的网络规则**，确保流量正确转发。

### 核心功能
- **流量转发**：将 Service IP 的流量转发到后端 Pod
- **负载均衡**：在多个 Pod 之间分发请求
- **维护 iptables/IPVS 规则**：底层网络规则管理

### 工作原理
```
# 场景：外部请求访问 API Service

1. 请求到达 Service：
   http://api-service:8000

2. Kube Proxy 选择后端 Pod（轮询）：
   api-pod-1 (10.244.1.20)  ← 第 1 次请求
   api-pod-2 (10.244.2.30)  ← 第 2 次请求
   api-pod-1 (10.244.1.20)  ← 第 3 次请求

3. 转发流量到选中的 Pod
```

### 代理模式
```bash
# iptables 模式（默认）
- 优点: 成熟稳定
- 缺点: 规则多时性能下降

# IPVS 模式（推荐大规模集群）
- 优点: 高性能，支持更多负载均衡算法
- 缺点: 需要内核支持
```

### 在 KnowledgeWeaver 中
```yaml
# API Service 配置（Kube Proxy 实现负载均衡）
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: knowledgeweaver-api
  ports:
    - port: 9621
      targetPort: 9621
  type: LoadBalancer  # Kube Proxy 配合 AWS LB 实现外部访问
```

**作用：**
- 请求 `api-service:9621` 自动分发到多个 API Pod
- 某个 Pod 故障时，自动从列表中移除
- 支持会话保持（Session Affinity）

---

## 5. VPC CNI Addon (容器网络接口)

### 是什么？
VPC CNI 是 AWS 特有的 **容器网络插件**，让 Pod 直接获得 VPC 内的真实 IP 地址。

### 核心功能
- **Pod IP 分配**：每个 Pod 获得 VPC 子网内的 IP
- **与 VPC 深度集成**：Pod 可以直接访问 VPC 内其他资源（RDS、ElastiCache）
- **安全组支持**：可以为 Pod 分配 EC2 安全组

### 与其他 CNI 的区别
```
# 标准 CNI（如 Calico）
Pod IP: 172.16.0.10 (虚拟网络)
Node IP: 10.0.1.5 (VPC 真实 IP)
  → Pod 通过 NAT 访问外部

# AWS VPC CNI
Pod IP: 10.0.1.20 (VPC 真实 IP)
Node IP: 10.0.1.5 (VPC 真实 IP)
  → Pod 直接参与 VPC 网络，无需 NAT
```

### IP 地址管理
```bash
# 每个节点的 IP 池
t3.medium 节点:
  - 主 ENI: 6 个 IP（1 个用于节点，5 个用于 Pod）
  - 辅助 ENI: 每个 6 个 IP
  - 最多支持: 17 个 Pod

# IP 不足时
1. VPC CNI 自动创建辅助 ENI
2. 从子网分配更多 IP
3. 分配给新 Pod
```

### 在 KnowledgeWeaver 中
```yaml
# Pod 直接获得 VPC IP
apiVersion: v1
kind: Pod
metadata:
  name: api-pod
spec:
  containers:
  - name: api
    image: knowledgeweaver-api:latest

# Pod 启动后
Pod IP: 10.0.1.25 (VPC 子网 10.0.1.0/24)

# 可以直接访问同 VPC 的 RDS（如果后续使用）
RDS Endpoint: postgres.abc123.us-west-2.rds.amazonaws.com (10.0.2.100)
```

**作用：**
- Pod 可以直接访问 VPC 内的其他 AWS 服务（无需额外配置）
- 支持 AWS 安全组控制 Pod 网络访问
- 简化网络架构，避免复杂的 NAT 规则

**注意事项：**
- 确保 VPC 子网有足够的 IP 地址
- IP 地址耗尽会导致 Pod 无法启动

---

## 6. EBS CSI Driver Addon (存储驱动)

### 是什么？
EBS CSI Driver 是 Kubernetes 的 **持久化存储驱动**，让 Pod 可以使用 AWS EBS（弹性块存储）卷。

### 核心功能
- **动态卷创建**：自动创建和挂载 EBS 卷
- **持久化数据**：Pod 重启或迁移，数据不丢失
- **快照和备份**：支持 EBS 快照功能
- **多种存储类型**：gp3、io2、st1 等

### 存储类型对比
```bash
# gp3（通用型 SSD，推荐）
- 性能: 3000 IOPS，125 MB/s
- 成本: 低
- 适用: Neo4j 数据库、日志存储

# io2（高性能 SSD）
- 性能: 最高 64000 IOPS，1000 MB/s
- 成本: 高
- 适用: 高负载数据库

# sc1（冷 HDD）
- 性能: 低
- 成本: 最低
- 适用: 归档数据、日志备份
```

### 工作原理
```
# 场景：Neo4j 需要持久化存储

1. 定义 PVC（Persistent Volume Claim）：
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: neo4j-data
   spec:
     accessModes: [ReadWriteOnce]
     resources:
       requests:
         storage: 50Gi
     storageClassName: gp3

2. EBS CSI Driver 自动：
   - 创建 50GB EBS 卷（在 AWS EC2 控制台可见）
   - 挂载到运行 Neo4j Pod 的节点
   - 映射到 Pod 容器内的路径

3. Neo4j 使用存储：
   数据写入 /var/lib/neo4j/data → EBS 卷
```

### 在 KnowledgeWeaver 中
```yaml
# Neo4j StatefulSet 配置
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
spec:
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: [ReadWriteOnce]
      storageClassName: gp3
      resources:
        requests:
          storage: 50Gi  # Neo4j 数据持久化

# API 服务也可以使用（可选）
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: api-logs
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi  # 日志持久化
```

**作用：**
- Neo4j 数据存储在 EBS，Pod 重启数据不丢失
- 支持数据快照备份（定期备份图谱数据）
- Pod 迁移到其他节点时，EBS 卷自动跟随

**注意事项：**
- EBS 卷只能挂载到单个 Pod（ReadWriteOnce）
- 卷和 Pod 必须在同一个可用区
- 删除 PVC 时，EBS 卷默认也会被删除（可配置保留策略）

---

## 组件依赖关系

### 启动顺序
```
第一阶段：基础设施
├── 1. EKS Cluster (控制平面)
│   └── 提供 API Server、调度器、etcd
│
└── 2. Node Group (工作节点)
    └── 提供计算资源（CPU、内存）

第二阶段：网络层（并行安装）
├── 3a. VPC CNI
│   └── 为 Pod 分配 IP 地址
│
└── 3b. Kube Proxy
    └── 实现 Service 负载均衡

第三阶段：应用层（并行安装）
├── 4a. CoreDNS
│   └── 依赖网络层，提供 DNS 解析
│
└── 4b. EBS CSI Driver
    └── 依赖网络层，提供持久化存储
```

### 数据流
```
用户请求
  ↓
[LoadBalancer]
  ↓
[Kube Proxy] ← 转发规则
  ↓
[API Pod] ← VPC CNI 分配 IP
  ↓
[CoreDNS] ← 解析 neo4j-service
  ↓
[Neo4j Pod] ← VPC CNI 分配 IP
  ↓
[EBS 卷] ← EBS CSI Driver 挂载
```

---

## 在 KnowledgeWeaver 中的应用

### 完整部署示例
```yaml
# 1. Neo4j 数据库（StatefulSet + PVC）
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
spec:
  serviceName: neo4j-service  # CoreDNS 注册服务名
  replicas: 1
  template:
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.23.0
        ports:
        - containerPort: 7687  # Kube Proxy 转发端口
        volumeMounts:
        - name: neo4j-data
          mountPath: /data     # EBS CSI Driver 挂载点
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: [ReadWriteOnce]
      storageClassName: gp3   # EBS CSI Driver 创建 EBS 卷
      resources:
        requests:
          storage: 50Gi

---
# 2. Neo4j Service（DNS 解析 + 负载均衡）
apiVersion: v1
kind: Service
metadata:
  name: neo4j-service          # CoreDNS 解析此名称
spec:
  clusterIP: 10.100.1.50       # VPC CNI 分配 ClusterIP
  selector:
    app: neo4j
  ports:
  - port: 7687
    targetPort: 7687           # Kube Proxy 转发到 Pod:7687

---
# 3. API 服务（Deployment + Service）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2                  # Kube Proxy 负载均衡 2 个 Pod
  template:
    spec:
      containers:
      - name: api
        image: knowledgeweaver-api:latest
        env:
        - name: NEO4J_URI
          value: "bolt://neo4j-service:7687"  # CoreDNS 解析
        ports:
        - containerPort: 9621  # VPC CNI 分配 Pod IP

---
# 4. API Service（外部访问）
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: LoadBalancer           # AWS 创建 ELB
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 9621           # Kube Proxy 转发到 Pod:9621
```

### 各组件作用总结
| 组件 | 在 KnowledgeWeaver 中的作用 |
|------|---------------------------|
| **EKS Cluster** | 接收 kubectl 命令，调度 Neo4j 和 API Pod |
| **Node Group** | 提供 2 个 t3.medium 节点运行服务 |
| **VPC CNI** | 为 Neo4j 和 API Pod 分配 VPC IP（如 10.0.1.20） |
| **Kube Proxy** | 负载均衡 2 个 API Pod，转发请求到健康实例 |
| **CoreDNS** | API 通过 `neo4j-service` 访问数据库，无需 IP |
| **EBS CSI Driver** | Neo4j 数据存储在 50GB EBS 卷，Pod 重启数据保留 |

---

## 监控和故障排查

### 检查组件状态
```bash
# 查看集群状态
kubectl cluster-info

# 查看节点状态
kubectl get nodes

# 查看系统 Pod（包括所有插件）
kubectl get pods -n kube-system

# 检查 CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 检查 Kube Proxy
kubectl get pods -n kube-system -l k8s-app=kube-proxy

# 检查 VPC CNI
kubectl get pods -n kube-system -l k8s-app=aws-node

# 检查 EBS CSI Driver
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

### 常见问题

#### 1. Pod 无法启动（Pending）
```bash
# 可能原因：IP 地址不足（VPC CNI）
kubectl describe pod <pod-name>

# 解决方案：扩展子网或减少 Pod 数量
```

#### 2. Pod 无法通过服务名访问（DNS 问题）
```bash
# 可能原因：CoreDNS 故障
kubectl logs -n kube-system -l k8s-app=kube-dns

# 解决方案：重启 CoreDNS
kubectl rollout restart deployment/coredns -n kube-system
```

#### 3. PVC 无法挂载（存储问题）
```bash
# 可能原因：EBS CSI Driver 未安装或故障
kubectl get pvc
kubectl describe pvc <pvc-name>

# 解决方案：检查 CSI Driver
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

#### 4. 负载均衡不工作（流量转发问题）
```bash
# 可能原因：Kube Proxy 规则未更新
kubectl get svc
kubectl describe svc <service-name>

# 解决方案：重启 Kube Proxy
kubectl rollout restart daemonset/kube-proxy -n kube-system
```

---

## 成本优化建议

### 节点选型
```bash
# 开发环境
instance_type: t3.medium  # $0.0416/小时
desired_size: 2 节点
月成本: ~$60

# 生产环境
instance_type: t3.large   # $0.0832/小时
desired_size: 3 节点
月成本: ~$180
```

### 存储优化
```bash
# Neo4j 数据卷
storageClassName: gp3     # $0.08/GB/月
storage: 50Gi
月成本: $4

# 日志卷（如果需要）
storageClassName: sc1     # $0.025/GB/月（冷存储）
storage: 100Gi
月成本: $2.5
```

### 自动伸缩
```hcl
# 节点自动伸缩
min_size = 1  # 夜间缩容到 1 个节点
max_size = 4  # 高峰期扩展到 4 个节点

# HPA（Pod 自动伸缩）
kubectl autoscale deployment api --min=2 --max=10 --cpu-percent=70
```

---

## 总结

### 关键要点
1. **EKS Cluster**：集群大脑，管理所有资源
2. **Node Group**：工作节点，提供计算资源
3. **VPC CNI**：网络基础，为 Pod 分配 IP
4. **Kube Proxy**：流量转发，实现负载均衡
5. **CoreDNS**：服务发现，通过名称访问服务
6. **EBS CSI Driver**：持久化存储，数据不丢失

### 最佳实践
- ✅ 使用 gp3 存储（性价比最高）
- ✅ 配置节点自动伸缩（节省成本）
- ✅ 为关键服务配置多副本（高可用）
- ✅ 定期备份 EBS 卷（数据安全）
- ✅ 监控 IP 地址使用情况（避免耗尽）

### 学习资源
- [AWS EKS 官方文档](https://docs.aws.amazon.com/eks/)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [VPC CNI 深入解析](https://github.com/aws/amazon-vpc-cni-k8s)
- [EBS CSI Driver 使用指南](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)

---

**文档版本**: 1.0.0
**更新日期**: 2026-01-29
**适用项目**: KnowledgeWeaver
**维护者**: Sheldon
