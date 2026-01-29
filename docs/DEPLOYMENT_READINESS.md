# Deployment Readiness Checklist

**Date**: 2026-01-29
**Status**: 🟡 Ready for EKS Deployment

---

## Summary

✅ **Docker Image**: Built and pushed to ECR
🟡 **AWS Infrastructure**: Waiting for stack redeployment
🟡 **Kubernetes Configs**: Updated, ready to apply
⏳ **Secrets**: Script ready, waiting for EKS cluster

---

## Completed Tasks ✅

### 1. Docker Image Build and Push

| Item | Status | Details |
|------|--------|---------|
| ECR Repository | ✅ Created | knowledgeweaver-api |
| Docker Build | ✅ Complete | Multi-stage build, 347 MB |
| Image Tags | ✅ Pushed | latest, v1.0.0 |
| Image URI | ✅ Ready | 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest |
| Image Digest | ✅ Verified | sha256:6bc8ce6f09a8a15bc4531a9c281847d7c8ea243b15ca7416e9adbb9a77790e11 |

**Build Details**:
- Base: python:3.11-slim
- Size: 347 MB (compressed), 1.13 GB (uncompressed)
- Layers: 9
- Dependencies: 100+ Python packages
- Health check: ✅ Configured

### 2. Kubernetes Configuration Updates

| File | Status | Changes |
|------|--------|---------|
| `api/deployment.yaml` | ✅ Updated | ECR image URI, GEMINI_API_KEY env var |
| `configmap.yaml` | ✅ Enhanced | Added LLM, Extraction, RAG configs |
| `secrets.yaml` | ✅ Template | Ready for values |

**Updated Configs**:
```yaml
# Deployment
image: 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest

# ConfigMap additions
LLM_BINDING_HOST: "https://space.ai-builders.com/backend/v1"
LLM_MODEL: "deepseek"
EXTRACTION_LLM_BACKEND: "gemini"
GEMINI_MODEL: "gemini-2.0-flash"
EMBEDDING_MODEL: "text-embedding-ada-002"
CHROMA_PERSIST_DIR: "/app/data/storage/vector_db"
```

### 3. Deployment Scripts

| Script | Status | Purpose |
|--------|--------|---------|
| `create-secrets.sh` | ✅ Created | Create Kubernetes secrets from .env |
| `install-alb-controller.sh` | ✅ Exists | Install AWS Load Balancer Controller |
| `deploy.sh` | ✅ Exists | Deploy Kubernetes manifests |

---

## Pending Tasks ⏳

### 1. AWS Infrastructure (CloudFormation)

**Current Status**: Stack in `ROLLBACK_COMPLETE` state

**Issue**: Deployed with OLD template (missing IRSA)
**Fix Applied**: ✅ Updated template uploaded to S3
**Next Action**: Redeploy stack

```bash
# 1. Delete failed stack
aws cloudformation delete-stack \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2

# 2. Wait for deletion (~5 minutes)
aws cloudformation wait stack-delete-complete \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2

# 3. Redeploy with corrected template
cd deploy/cloudformation/scripts
bash deploy.sh
# Expected time: 15-20 minutes
```

**What's in the Fixed Template**:
- ✅ OIDC Identity Provider
- ✅ EBS CSI Driver IAM Role with IRSA
- ✅ ServiceAccountRoleArn configured
- ✅ No EBS policy on node role (security best practice)

### 2. Kubernetes Deployment

**After EKS cluster is ready**:

```bash
# 1. Update kubeconfig
aws eks update-kubeconfig \
  --region ap-southeast-2 \
  --name knowledgeweaver-production

# 2. Verify cluster access
kubectl cluster-info
kubectl get nodes

# 3. Create secrets
cd deploy/kubernetes/scripts
bash create-secrets.sh

# 4. Deploy application
kubectl apply -k deploy/kubernetes/base/

# 5. Verify deployment
kubectl get all -n prod
kubectl get pvc -n prod
kubectl logs -n prod -l app=api

# 6. Install AWS Load Balancer Controller
bash install-alb-controller.sh

# 7. Get application URL
kubectl get ingress -n prod
```

### 3. Post-Deployment Verification

```bash
# Check pod status
kubectl get pods -n prod -w

# View API logs
kubectl logs -n prod -l app=api -f

# Test health endpoints
ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$ALB_URL/health
curl http://$ALB_URL/ready

# Test API endpoint
curl http://$ALB_URL/api/stats

# Access observability dashboards
echo "Langfuse: http://$ALB_URL/langfuse"
echo "Phoenix: http://$ALB_URL/phoenix"
```

---

## Configuration Status

### Environment Variables

**ConfigMap** (Non-sensitive):
- ✅ Application settings (HOST, PORT)
- ✅ Neo4j connection (URI, user, pool settings)
- ✅ Processing settings (concurrency, chunk size)
- ✅ LLM configuration (host, models)
- ✅ RAG configuration (embedding, chunk settings)
- ✅ Observability (Phoenix, Langfuse)

**Secrets** (Sensitive):
- ⏳ NEO4J_PASSWORD (from .env)
- ⏳ LLM_BINDING_API_KEY (from .env)
- ⏳ GEMINI_API_KEY (from .env)
- ⏳ LANGFUSE_PUBLIC_KEY (from .env)
- ⏳ LANGFUSE_SECRET_KEY (from .env)
- ⏳ Langfuse internal secrets (auto-generated)

**Secret Creation Script**: `deploy/kubernetes/scripts/create-secrets.sh`
- ✅ Reads from .env file
- ✅ Creates knowledgeweaver-secrets
- ✅ Auto-generates Langfuse secrets
- ⏳ Ready to run after EKS deployment

### Storage Configuration

**Neo4j StatefulSet**:
- ✅ PersistentVolumeClaims configured
- ✅ Storage class: gp3 (AWS EBS)
- ✅ Data volume: 20 GB
- ✅ Logs volume: 5 GB
- ⚠️ Requires working EBS CSI Driver (will be fixed with IRSA)

**API Deployment**:
- ⚠️ Currently uses emptyDir (ephemeral)
- 📝 Recommendation: Create PVC for /app/data

**Suggested PVC for API**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: api-data-pvc
  namespace: prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi
```

---

## Deployment Sequence

### Phase 1: Infrastructure (EKS) ⏳

1. ⏳ Delete failed CloudFormation stack
2. ⏳ Redeploy with fixed template (IRSA enabled)
3. ⏳ Wait for EKS cluster creation (~15 minutes)
4. ⏳ Wait for node group creation (~5 minutes)
5. ⏳ Wait for EBS CSI Driver addon (~2 minutes)

**Expected Duration**: 20-25 minutes

### Phase 2: Application Deployment ⏳

1. ⏳ Configure kubectl
2. ⏳ Create namespace
3. ⏳ Create secrets from .env
4. ⏳ Deploy Kubernetes resources
5. ⏳ Install ALB Controller
6. ⏳ Wait for pods to be ready (~2 minutes)
7. ⏳ Verify ingress and ALB creation (~3 minutes)

**Expected Duration**: 5-10 minutes

### Phase 3: Verification ⏳

1. ⏳ Check pod status
2. ⏳ Test health endpoints
3. ⏳ Verify Neo4j connection
4. ⏳ Test document upload
5. ⏳ Verify observability dashboards

**Expected Duration**: 5 minutes

**Total Deployment Time**: 30-40 minutes

---

## Resource Requirements

### Per-Service Resources

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Storage |
|---------|-------------|-----------|----------------|--------------|---------|
| API (x2) | 250m | 1000m | 512Mi | 1Gi | emptyDir |
| Neo4j | 500m | 2000m | 2Gi | 4Gi | 25Gi PVC |
| Postgres | 250m | 500m | 256Mi | 512Mi | 10Gi PVC |
| Langfuse | 200m | 500m | 256Mi | 512Mi | - |
| Phoenix | 200m | 500m | 256Mi | 512Mi | 5Gi PVC |

**Total Cluster Requirements**:
- CPU: ~2.5 cores (requests), ~8 cores (limits)
- Memory: ~6.5 GB (requests), ~12 GB (limits)
- Storage: ~40 GB PVCs

**Node Group**: 2x t3.medium (2 vCPU, 4 GB each)
- Total: 4 vCPU, 8 GB memory
- Status: ✅ Adequate for initial deployment
- Note: May need scaling for production load

---

## Cost Estimation

### AWS Infrastructure

| Component | Cost | Billing |
|-----------|------|---------|
| EKS Control Plane | $73/month | Fixed |
| 2x t3.medium nodes | $30/month each | When running |
| EBS volumes (40 GB) | $4/month | gp3 storage |
| NAT Gateways (2x) | $65/month | Fixed |
| ALB | $20/month | When deployed |
| ECR storage (347 MB) | $0.03/month | Negligible |
| **Total (Running)** | **~$222/month** | Full deployment |
| **Total (Stopped)** | **~$160/month** | Nodes scaled to 0 |

### Cost Optimization Options

1. **Scale nodes to zero** when not in use:
   ```bash
   aws eks update-nodegroup-config \
     --cluster-name knowledgeweaver-production \
     --nodegroup-name main-nodes \
     --scaling-config desiredSize=0,minSize=0
   ```
   Saves: $60/month

2. **Remove NAT Gateways** (use public subnets only):
   - Saves: $65/month
   - Trade-off: Less secure (nodes have public IPs)

3. **Use smaller nodes** (t3.small):
   - Saves: $15/month
   - Trade-off: Less capacity, may need 3 nodes

---

## Known Issues and Mitigations

### Issue 1: API Data Persistence ⚠️

**Problem**: API uses emptyDir, loses data on pod restart
**Impact**: Uploaded documents and checkpoints lost
**Mitigation**: Create PVC for /app/data (see Storage Configuration)
**Priority**: Medium (workable for demo, critical for production)

### Issue 2: Secrets in Git 🔒

**Problem**: .env file contains secrets
**Impact**: Security risk if committed
**Mitigation**: .env in .gitignore, use AWS Secrets Manager for production
**Priority**: High (before production deployment)

### Issue 3: No Backup Strategy 💾

**Problem**: No automated backups configured
**Impact**: Data loss if volumes fail
**Mitigation**: Configure EBS snapshots or Velero
**Priority**: Medium (for production)

### Issue 4: No Monitoring/Alerting 📊

**Problem**: No CloudWatch metrics or alarms
**Impact**: No visibility into cluster health
**Mitigation**: Install CloudWatch Container Insights
**Priority**: Medium (nice to have)

---

## Next Immediate Actions

### 1. Redeploy CloudFormation Stack (Required)

```bash
# Check current stack status
aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2 \
  --query 'Stacks[0].StackStatus'

# If ROLLBACK_COMPLETE, delete it
aws cloudformation delete-stack \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2

# Redeploy
cd deploy/cloudformation/scripts
bash deploy.sh
```

**Monitor Progress**:
```bash
# Watch stack events
watch -n 10 'aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2 \
  --query "Stacks[0].StackStatus"'

# Or use status script
bash deploy/scripts/status-all.sh
```

### 2. Deploy Application (After EKS Ready)

```bash
# 1. Configure kubectl
aws eks update-kubeconfig \
  --region ap-southeast-2 \
  --name knowledgeweaver-production

# 2. Deploy everything
cd deploy/kubernetes/scripts
bash create-secrets.sh
bash deploy.sh

# 3. Monitor deployment
kubectl get pods -n prod -w
```

### 3. Verify and Test

```bash
# Get ingress URL
ALB_URL=$(kubectl get ingress knowledgeweaver-ingress -n prod \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test endpoints
curl http://$ALB_URL/health
curl http://$ALB_URL/api/stats

# Upload test document
curl -X POST http://$ALB_URL/api/documents/upload-async \
  -F "file=@tests/data/test_small.txt"
```

---

## Documentation

### Generated Documentation

- ✅ `CONFIGURATION_REVIEW.md` - Complete config review
- ✅ `EKS_IRSA_FIX.md` - IRSA implementation details
- ✅ `DOCKER_IMAGE_BUILD.md` - Image build process
- ✅ `DEPLOYMENT_READINESS.md` - This document

### Existing Documentation

- `README.md` - Project overview
- `CLAUDE.md` - Project configuration
- `docs/NEO4J_GUIDE.md` - Neo4j usage guide
- `docs/LANGFUSE_GUIDE.md` - Langfuse integration
- `docs/AWS_DEPLOYMENT_GUIDE.md` - AWS deployment guide

---

## Success Criteria

### Deployment Successful When:

- ✅ CloudFormation stack: CREATE_COMPLETE
- ✅ EKS cluster: ACTIVE
- ✅ Worker nodes: 2 nodes READY
- ✅ EBS CSI Driver: ACTIVE with IRSA
- ✅ All pods: Running and Ready (2/2)
- ✅ Neo4j: Connected and responsive
- ✅ API health: /health returns 200
- ✅ Ingress: ALB created with public URL
- ✅ Document upload: Successfully processes test file
- ✅ Graph query: Returns results from Neo4j

### Verification Commands

```bash
# Infrastructure
aws eks describe-cluster --name knowledgeweaver-production --region ap-southeast-2
aws eks describe-nodegroup --cluster-name knowledgeweaver-production --nodegroup-name main-nodes --region ap-southeast-2
aws eks describe-addon --cluster-name knowledgeweaver-production --addon-name aws-ebs-csi-driver --region ap-southeast-2

# Kubernetes
kubectl get nodes
kubectl get all -n prod
kubectl get pvc -n prod
kubectl get ingress -n prod

# Application
curl http://$ALB_URL/health | jq
curl http://$ALB_URL/api/stats | jq
```

---

**Status**: 🟡 Ready for EKS deployment
**Blocker**: CloudFormation stack needs redeployment
**ETA**: 30-40 minutes after redeployment starts

**Last Updated**: 2026-01-29 13:50 NZDT
**Maintained By**: Sheldon
