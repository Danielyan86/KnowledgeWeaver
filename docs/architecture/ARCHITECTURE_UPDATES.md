# Architecture Updates - Demo Environment

**Date**: 2026-01-29
**Version**: 2.0 (Demo/Interview Configuration)
**Maintainer**: Sheldon

---

## Overview

Updated the architecture from production multi-replica setup to a **simplified demo/interview environment** for easier demonstration and cost optimization.

---

## Key Changes

### 1. Environment Configuration

| Aspect | Before | After |
|--------|--------|-------|
| **Target Environment** | Production (multi-AZ) | Demo/Interview (single environment) |
| **Namespace** | `prod` | `demo` |
| **API Replicas** | 2 (static) | 1 (auto-scales 1-3) |
| **Deployment Strategy** | Kustomize overlays (dev/prod) | Single base configuration |
| **Cost/Month** | ~$92-128 | ~$60-80 (8 hrs/day) |

### 2. Architecture Diagrams

#### Updated: AWS Architecture Diagrams

**Removed:**
- ❌ AWS Cloud outer layer (cleaner visualization)
- ❌ Internet Users hexagon (simplified entry point)
- ❌ EKS Control Plane box (AWS managed, not shown)

**Updated:**
- ✅ VPC and subnet layout improved
- ✅ Better component spacing and alignment
- ✅ 2-column grid for AWS Managed Services
- ✅ Canvas size: 1400x850 → 1600x850
- ✅ Subtitle: "ECS Fargate 演示环境部署"

**Components:**
- API Pod: 1 replica (centered on Worker Node 1)
- Neo4j: Graph database on Worker Node 2
- Observability: Phoenix, Langfuse, PostgreSQL (optional)
- AWS Services: S3, ECR, RDS, CloudWatch, Secrets Manager, SNS, CloudTrail

#### Files Updated:
- `aws-architecture-diagram-en.html` - English interactive diagram
- `aws-architecture-diagram-cn.html` - Chinese interactive diagram

### 3. Storage Layer Corrections

**Before:**
```
Storage Layer:
- JSON file storage  ❌
- ChromaDB vector database
```

**After:**
```
Storage Layer:
- Neo4j graph database (knowledge graph storage)  ✅
- ChromaDB vector database (semantic search)
```

**Impact:**
- Updated all documentation references
- Corrected architecture diagrams
- Updated README.md to reflect actual implementation

### 4. Kubernetes Configuration

#### Removed:
```
deploy/kubernetes/
├── overlays/
│   ├── dev/
│   └── prod/
```

**Reason**: Overcomplicated for demo project

#### Updated All Manifests:
- Changed `namespace: prod` → `namespace: demo`
- Updated API deployment: `replicas: 2` → `replicas: 1`
- Updated HPA: `minReplicas: 2, maxReplicas: 5` → `minReplicas: 1, maxReplicas: 3`

### 5. Public Access Configuration

#### Added Three Access Methods:

**1. LoadBalancer Service (Recommended for Demo)**
```yaml
# File: deploy/kubernetes/base/api/service-loadbalancer.yaml
type: LoadBalancer
port: 80 → targetPort: 9621
annotations:
  service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

**2. Ingress + ALB Controller**
```yaml
# File: deploy/kubernetes/base/ingress.yaml
annotations:
  kubernetes.io/ingress.class: alb
  alb.ingress.kubernetes.io/scheme: internet-facing
```

**3. NodePort**
```yaml
# File: deploy/kubernetes/base/api/service-nodeport.yaml
type: NodePort
nodePort: 30621
```

#### New Documentation:
- `deploy/kubernetes/PUBLIC_ACCESS_GUIDE.md` - Complete guide with all three methods
- `deploy/kubernetes/scripts/install-alb-controller.sh` - ALB Controller installation script

---

## Architecture Comparison

### Before: Production Setup

```
Production Environment
├── Namespace: prod
├── API Pods: 2 replicas (static)
├── HPA: 2-5 replicas
├── Deployment: Kustomize overlays (dev/prod)
├── Access: Ingress + ALB only
└── Cost: ~$92-128/month (24/7)
```

### After: Demo Setup

```
Demo Environment
├── Namespace: demo
├── API Pods: 1 replica (auto-scales 1-3)
├── Deployment: Simple base manifests
├── Access: 3 options (LoadBalancer/Ingress/NodePort)
└── Cost: ~$60-80/month (8 hrs/day)
```

---

## Visual Changes

### AWS Architecture Diagram Flow

**Before:**
```
Internet Users
    ↓
Internet Gateway
    ↓
AWS Cloud
    ↓
VPC
    ↓
EKS Control Plane
    ↓
ALB → 2x API Pods
```

**After:**
```
Internet Gateway
    ↓
VPC
├── Public Subnet
│   ├── ALB
│   └── NAT Gateway
└── Private Subnet / EKS Cluster
    ├── Worker Node 1 → 1x API Pod
    └── Worker Node 2 → Neo4j Pod
```

---

## Migration Impact

### ✅ Backwards Compatible
- All existing features work
- No breaking changes to application code
- Can scale back to production setup easily

### ✅ Cost Savings
- **Production 24/7**: ~$173/month
- **Demo 8hrs/day**: ~$60-80/month
- **Savings**: ~60% cost reduction

### ✅ Simplified Deployment
```bash
# Before (with overlays)
kubectl apply -k deploy/kubernetes/overlays/prod

# After (simpler)
kubectl apply -k deploy/kubernetes/base
```

---

## File Changes Summary

### Created Files:
1. `deploy/kubernetes/base/api/service-loadbalancer.yaml`
2. `deploy/kubernetes/base/api/service-nodeport.yaml`
3. `deploy/kubernetes/scripts/install-alb-controller.sh`
4. `deploy/kubernetes/PUBLIC_ACCESS_GUIDE.md`
5. `deploy/kubernetes/README.md`
6. `docs/architecture/ARCHITECTURE_UPDATES.md` (this file)

### Modified Files:
1. `deploy/kubernetes/base/namespace.yaml` - Changed to `demo`
2. `deploy/kubernetes/base/api/deployment.yaml` - 1 replica
3. `deploy/kubernetes/base/api/hpa.yaml` - 1-3 replicas
4. All other k8s manifests (16 files) - Updated namespace
5. `docs/architecture/aws-architecture-diagram-en.html` - Updated diagram
6. `docs/architecture/aws-architecture-diagram-cn.html` - Updated diagram
7. `docs/architecture/README.md` - Updated documentation
8. `README.md` - Updated storage layer info
9. `README_CN.md` - Updated storage layer info

### Deleted:
1. `deploy/kubernetes/overlays/` - Entire directory (dev/prod)

---

## Deployment Guide

### Quick Deploy

```bash
# 1. Deploy application
kubectl apply -k deploy/kubernetes/base/

# 2. Enable public access (choose one):

# Option A: LoadBalancer (recommended)
kubectl apply -f deploy/kubernetes/base/api/service-loadbalancer.yaml

# Option B: Ingress + ALB
./deploy/kubernetes/scripts/install-alb-controller.sh
kubectl apply -f deploy/kubernetes/base/ingress.yaml

# Option C: NodePort
kubectl apply -f deploy/kubernetes/base/api/service-nodeport.yaml

# 3. Get public URL
kubectl get svc api-public -n demo  # For LoadBalancer
kubectl get ingress -n demo         # For Ingress
```

### Access the API

```bash
# Get URL
LB_URL=$(kubectl get svc api-public -n demo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test
curl http://${LB_URL}/health
open http://${LB_URL}/docs
```

---

## OIDC/IRSA Configuration

### Understanding OIDC in EKS

The demo environment uses **OIDC (OpenID Connect)** for secure pod authentication via **IRSA (IAM Roles for Service Accounts)**.

**Flow:**
1. **Deploy**: CloudFormation creates OIDC Provider (uses your local AWS credentials)
2. **Runtime**: Pods use JWT tokens (no static credentials needed)
3. **Security**: Each Service Account has unique IAM role with minimal permissions

**Key Files:**
- `deploy/cloudformation/templates/eks.yaml` - OIDC Provider configuration
- `docs/deployment/EKS_IRSA_FIX.md` - Detailed OIDC explanation

**Benefits:**
- ✅ No Access Keys in pods
- ✅ Temporary credentials (15min tokens, 1hr temp creds)
- ✅ Fine-grained permissions per Service Account
- ✅ Automatic credential rotation

---

## Recommendations

### For Demo/Interview:
✅ Use the current demo configuration
✅ Enable LoadBalancer for easy access
✅ Stop cluster when not in use
✅ Keep observability tools optional

### To Scale to Production:
1. Change namespace to `prod`
2. Increase API replicas to 2-3
3. Update HPA to `minReplicas: 2, maxReplicas: 10`
4. Use Ingress + ALB for advanced routing
5. Enable SSL/TLS with ACM certificate
6. Add persistent volumes for data
7. Implement backup strategy
8. Enable multi-AZ deployment

---

## References

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Cost Optimization](https://www.kubecost.com/kubernetes-cost-optimization/)
- [IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)

---

**Next Steps:**
1. Review [Public Access Guide](../../deploy/kubernetes/PUBLIC_ACCESS_GUIDE.md)
2. Deploy using [Kubernetes README](../../deploy/kubernetes/README.md)
3. Configure access method
4. Test API endpoints
5. (Optional) Set up observability tools

