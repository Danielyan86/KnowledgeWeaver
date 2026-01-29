# KnowledgeWeaver Configuration Review

**Date**: 2026-01-29
**Status**: AWS Deployment In Progress (ROLLBACK_COMPLETE - needs redeployment)

## 🚨 Critical Issue Discovered

**Problem**: The CloudFormation stack deployed with OLD templates from S3 cache
**Impact**: EBS CSI Driver deployed WITHOUT IRSA, causing the same failure again
**Root Cause**: Deploy script used cached S3 templates (6.4 KB) instead of updated local templates (8.2 KB)

### Timeline
1. ✅ Fixed eks.yaml locally with IRSA configuration
2. ❌ Deployed stack using cached S3 template (missing IRSA)
3. ❌ EBS CSI Driver failed again - no ServiceAccountRole
4. ✅ Uploaded updated template to S3 (now 8.0 KB)
5. ⏳ Need to redeploy stack with correct template

---

## Configuration Files Overview

### 1. Environment Configuration

#### `.env` (Local Development)
```bash
# LLM Configuration
LLM_BINDING_HOST=https://space.ai-builders.com/backend/v1
LLM_BINDING_API_KEY=sk_bc200441_*** (包月服务)
LLM_MODEL=deepseek

# Extraction Engine
EXTRACTION_LLM_BACKEND=gemini
GEMINI_API_KEY=AIzaSyBlVkE2TYa*** (免费)
GEMINI_MODEL=gemini-2.0-flash

# Concurrency
CONCURRENT_REQUESTS=5
MAX_RETRIES=3
CHUNK_SIZE=800
CHUNK_OVERLAP_RATIO=0.5

# Neo4j
USE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=admin654321

# Observability
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3000
PHOENIX_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:4317
```

**⚠️ Security Issues**:
- API keys hardcoded in .env (should use AWS Secrets Manager in production)
- Neo4j password in plaintext

**✅ Good Practices**:
- Separate LLM for Q&A (paid) vs extraction (free Gemini)
- Observability enabled (Langfuse + Phoenix)

---

### 2. AWS CloudFormation Configuration

#### `deploy/cloudformation/parameters.json`
```json
{
  "ProjectName": "knowledgeweaver",
  "Environment": "production",
  "VpcCIDR": "10.0.0.0/16",
  "ClusterVersion": "1.31",
  "NodeInstanceType": "t3.medium",
  "NodeGroupMinSize": 0,
  "NodeGroupMaxSize": 5,
  "NodeGroupDesiredSize": 2,
  "LogRetentionDays": 7,
  "CostAlertThreshold": 5
}
```

**Configuration Analysis**:
- ✅ **ClusterVersion**: 1.31 (latest stable)
- ✅ **NodeGroupMinSize**: 0 (cost-optimized, can scale to zero)
- ✅ **NodeGroupDesiredSize**: 2 (redundancy for production)
- ✅ **LogRetentionDays**: 7 (short retention for demo)
- ⚠️ **NodeInstanceType**: t3.medium (may need upgrade for production load)

**Estimated Costs**:
- EKS Control Plane: $73/month (fixed)
- 2x t3.medium nodes: ~$60/month (when running)
- EBS volumes: ~$5-10/month
- **Total**: ~$140/month when running, $73/month when scaled to zero

---

### 3. CloudFormation Templates

#### Main Stack (`main.yaml`)
```yaml
Resources:
  - VPCStack (nested)
  - EKSStack (nested)
  - ECRStack (nested)
  - S3Stack (nested)
  - CloudWatchStack (nested)
```

**Current Status**:
| Stack | Status | Notes |
|-------|--------|-------|
| VPCStack | ✅ CREATE_COMPLETE | Network ready |
| S3Stack | ✅ CREATE_COMPLETE | Template storage ready |
| ECRStack | ✅ CREATE_COMPLETE | Container registry ready |
| EKSStack | ❌ DELETE_COMPLETE | Failed and rolled back |
| Main | ❌ ROLLBACK_COMPLETE | Needs redeployment |

#### EKS Stack (`eks.yaml`) - **UPDATED**

**Local File** (8.2 KB) - ✅ **Correct version with IRSA**:
```yaml
Resources:
  EKSCluster: # Kubernetes control plane
  OIDCProvider: # IRSA authentication ✅ NEW
  EBSCSIDriverRole: # Dedicated IAM role ✅ NEW
  NodeGroupRole: # Worker node role (no EBS policy) ✅ FIXED
  NodeGroup: # Worker nodes
  EBSCSIDriverAddon: # With ServiceAccountRoleArn ✅ FIXED
  VPCCNIAddon: # Network plugin
  CoreDNSAddon: # DNS
  KubeProxyAddon: # Proxy
```

**S3 File** (8.0 KB) - ✅ **Now updated**:
- Uploaded at: 2026-01-29 11:49:28
- Contains: OIDC Provider + EBS CSI Driver Role + proper IRSA config

#### VPC Stack (`vpc.yaml`)
```yaml
Resources:
  VPC: 10.0.0.0/16
  PublicSubnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
  PrivateSubnets: 10.0.11.0/24, 10.0.12.0/24 (2 AZs)
  InternetGateway: For public access
  NATGateways: 2x (one per AZ for HA)
```

**Status**: ✅ Deployed successfully

---

### 4. Kubernetes Configuration

#### Namespace (`base/namespace.yaml`)
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod
```

#### ConfigMap (`base/configmap.yaml`)
```yaml
data:
  HOST: "0.0.0.0"
  PORT: "9621"
  USE_NEO4J: "true"
  NEO4J_URI: "bolt://neo4j:7687"  # Internal service DNS
  CONCURRENT_REQUESTS: "5"
  PHOENIX_ENABLED: "true"
  PHOENIX_COLLECTOR_ENDPOINT: "http://phoenix:4317"
  LANGFUSE_ENABLED: "true"
  LANGFUSE_HOST: "http://langfuse:3000"
```

**⚠️ Issues**:
- Missing LLM configuration (API keys should be in secrets)
- Missing GEMINI_API_KEY reference

#### API Deployment (`base/api/deployment.yaml`)
```yaml
spec:
  replicas: 2
  containers:
  - name: api
    image: PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest
    ports:
    - containerPort: 9621
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "1000m"
    envFrom:
    - configMapRef:
        name: knowledgeweaver-config
    env:
    - name: NEO4J_PASSWORD
      valueFrom:
        secretKeyRef:
          name: knowledgeweaver-secrets
          key: NEO4J_PASSWORD
    volumeMounts:
    - name: data
      mountPath: /app/data
  volumes:
  - name: data
    emptyDir: {}  # ⚠️ Ephemeral! Need PVC for persistence
```

**⚠️ Critical Issues**:
1. **Image**: Uses PLACEHOLDER - needs ECR repository URL
2. **Storage**: Uses emptyDir (loses data on pod restart)
3. **Missing secrets**: LLM_BINDING_API_KEY, GEMINI_API_KEY not configured

**Recommendations**:
```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: api-data-pvc  # Need to create PVC
```

#### Neo4j StatefulSet (`base/neo4j/statefulset.yaml`)
```yaml
spec:
  replicas: 1
  containers:
  - name: neo4j
    image: neo4j:5-community
    env:
    - name: NEO4J_PLUGINS
      value: '["apoc", "graph-data-science"]'
    - name: NEO4J_dbms_memory_heap_max__size
      value: "2G"
    resources:
      requests:
        memory: "2Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "2000m"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      storageClassName: gp3  # ⚠️ Requires EBS CSI Driver!
      resources:
        requests:
          storage: 20Gi
```

**✅ Good Configuration**:
- Uses StatefulSet (stateful workload)
- PersistentVolumeClaims for data persistence
- APOC + GDS plugins enabled
- Proper resource limits

**❌ Blocker**: Requires working EBS CSI Driver (currently broken)

#### Ingress (`base/ingress.yaml`)
```yaml
metadata:
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /api
        backend:
          service:
            name: api
            port: 9621
      - path: /phoenix
        backend:
          service:
            name: phoenix
            port: 6006
      - path: /langfuse
        backend:
          service:
            name: langfuse
            port: 3000
```

**⚠️ Issue**: Requires AWS Load Balancer Controller (not installed yet)

---

## Current AWS Deployment Status

### CloudFormation Stack: `knowledgeweaver-production`

| Component | Status | Details |
|-----------|--------|---------|
| **Main Stack** | ❌ `ROLLBACK_COMPLETE` | Failed due to EKS stack issue |
| **VPC** | ✅ Active | 10.0.0.0/16, 2 AZs, 4 subnets |
| **S3 Bucket** | ✅ Active | knowledgeweaver-cfn-templates-1769596134 |
| **ECR Repository** | ✅ Active | Ready for Docker images |
| **EKS Cluster** | ❌ Deleted | Rolled back due to addon failure |
| **Worker Nodes** | ❌ None | Never created |
| **EBS CSI Driver** | ❌ Failed | No IRSA (old template used) |

### What Went Wrong

```
┌─────────────────────────────────────────────────────────┐
│ 1. Fixed eks.yaml locally (8.2 KB)                     │
│    ✅ Added OIDCProvider                                │
│    ✅ Added EBSCSIDriverRole                            │
│    ✅ Updated EBSCSIDriverAddon with ServiceAccountRole │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Ran deploy.sh                                        │
│    ❌ Script used CACHED S3 template (6.4 KB, old)     │
│    ❌ Did not upload new template to S3 first          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 3. CloudFormation deployed OLD template                │
│    ❌ No OIDCProvider created                           │
│    ❌ No EBSCSIDriverRole created                       │
│    ❌ EBSCSIDriverAddon without ServiceAccountRole      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 4. EBS CSI Driver pods crashed                         │
│    Error: "failed to refresh cached credentials"       │
│    Status: CrashLoopBackOff                            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Stack rolled back                                    │
│    Main Stack: ROLLBACK_COMPLETE                       │
│    EKS Stack: DELETE_COMPLETE                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 6. NOW: Uploaded correct template to S3 (8.0 KB)       │
│    ✅ Ready for redeployment                            │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration Issues Summary

### 🔴 Critical (Blocks Deployment)

1. **EBS CSI Driver IRSA**
   - Status: ✅ FIXED in template, uploaded to S3
   - Action: Redeploy stack

2. **API Container Image**
   - Issue: Uses PLACEHOLDER_ECR_REPO
   - Impact: Cannot deploy API pods
   - Fix Needed: Build and push Docker image to ECR

3. **Kubernetes Secrets**
   - Issue: Missing LLM API keys in secrets.yaml
   - Impact: API pods will fail without credentials
   - Fix Needed: Create secrets from .env values

### 🟡 High Priority (Affects Functionality)

4. **API Data Persistence**
   - Issue: Uses emptyDir (ephemeral storage)
   - Impact: Data loss on pod restart
   - Fix Needed: Create PVC for /app/data

5. **AWS Load Balancer Controller**
   - Issue: Not installed
   - Impact: Ingress won't create ALB
   - Fix Needed: Install ALB controller with IRSA

### 🟢 Medium Priority (Nice to Have)

6. **Secrets Management**
   - Issue: API keys in .env plaintext
   - Recommendation: Use AWS Secrets Manager
   - Benefit: Better security, rotation

7. **Monitoring**
   - Issue: No CloudWatch integration
   - Recommendation: Add CloudWatch Container Insights
   - Benefit: Better observability

8. **Auto-scaling**
   - Issue: HPA configured but needs metrics-server
   - Recommendation: Install metrics-server
   - Benefit: Auto-scale based on CPU/memory

---

## Deployment Checklist

### Step 1: Clean Up Failed Stack ✅ Done
```bash
aws cloudformation delete-stack --stack-name knowledgeweaver-production
# Wait for completion
```

### Step 2: Upload Updated Templates ✅ Done
```bash
aws s3 cp deploy/cloudformation/templates/eks.yaml s3://knowledgeweaver-cfn-templates-1769596134/
# Verified: 8.0 KB
```

### Step 3: Redeploy Stack ⏳ Ready
```bash
cd deploy/cloudformation/scripts
bash deploy.sh
# Estimated time: 15-20 minutes
```

### Step 4: Build and Push Docker Image ⏳ Pending
```bash
# Get ECR repository URL
ECR_REPO=$(aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryUri`].OutputValue' \
  --output text)

# Build image
docker build -t $ECR_REPO:latest -f deploy/docker/api/Dockerfile .

# Login and push
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin $ECR_REPO
docker push $ECR_REPO:latest
```

### Step 5: Create Kubernetes Secrets ⏳ Pending
```bash
# Update kubeconfig
aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production

# Create namespace
kubectl create namespace prod

# Create secrets from .env
kubectl create secret generic knowledgeweaver-secrets \
  --from-literal=NEO4J_PASSWORD=admin654321 \
  --from-literal=LLM_BINDING_API_KEY=sk_bc200441_*** \
  --from-literal=GEMINI_API_KEY=AIzaSyBlVkE2TYa*** \
  --from-literal=LANGFUSE_PUBLIC_KEY=pk-lf-*** \
  --from-literal=LANGFUSE_SECRET_KEY=sk-lf-*** \
  --namespace prod
```

### Step 6: Update Kubernetes Manifests ⏳ Pending
```bash
# Update API deployment with ECR image
sed -i "s|PLACEHOLDER_ECR_REPO|$ECR_REPO|g" \
  deploy/kubernetes/base/api/deployment.yaml

# Apply configurations
kubectl apply -k deploy/kubernetes/base/
```

### Step 7: Install AWS Load Balancer Controller ⏳ Pending
```bash
bash deploy/kubernetes/scripts/install-alb-controller.sh
```

### Step 8: Verify Deployment ⏳ Pending
```bash
# Check all pods
kubectl get pods -n prod

# Check PVCs
kubectl get pvc -n prod

# Check ingress
kubectl get ingress -n prod

# Get ALB URL
ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Application URL: http://$ALB_URL"
```

---

## Recommended Next Steps

1. **Immediate**: Redeploy CloudFormation stack with corrected template
2. **After deployment**: Build and push Docker image to ECR
3. **Then**: Deploy Kubernetes resources
4. **Finally**: Test end-to-end functionality

---

## Configuration Best Practices Applied

✅ **Infrastructure as Code**: All infrastructure in CloudFormation
✅ **Cost Optimization**: Node group can scale to zero
✅ **High Availability**: Multi-AZ deployment
✅ **Security**: IRSA for pod-level IAM permissions
✅ **Observability**: Langfuse + Phoenix integration
✅ **Scalability**: HPA configured for auto-scaling

## Configuration Issues to Address

❌ **Secrets Management**: Move to AWS Secrets Manager
❌ **Image Registry**: Need to build and push Docker images
❌ **Persistent Storage**: API needs PVC, not emptyDir
❌ **Monitoring**: Add CloudWatch Container Insights
❌ **Documentation**: Update deployment docs with ECR steps

---

**Document Status**: Current as of 2026-01-29 11:50 NZDT
**Next Update**: After successful redeployment
