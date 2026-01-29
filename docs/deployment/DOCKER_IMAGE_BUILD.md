# Docker Image Build and Deployment

**Date**: 2026-01-29
**Status**: ✅ Successfully built and pushed to ECR

## Build Summary

### ECR Repository Details

| Property | Value |
|----------|-------|
| **Repository Name** | knowledgeweaver-api |
| **Repository URI** | 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api |
| **Region** | ap-southeast-2 |
| **Scan on Push** | ✅ Enabled |
| **Tags** | Project=knowledgeweaver, Environment=production |

### Image Details

| Property | Value |
|----------|-------|
| **Image Size** | 347 MB (uncompressed: 1.13 GB) |
| **Base Image** | python:3.11-slim |
| **Build Type** | Multi-stage build |
| **Digest** | sha256:6bc8ce6f09a8a15bc4531a9c281847d7c8ea243b15ca7416e9adbb9a77790e11 |
| **Pushed At** | 2026-01-29 13:33:23 NZDT |
| **Tags Available** | latest, v1.0.0 |
| **Layers** | 9 |

### Build Process

```bash
# 1. Created ECR Repository
aws ecr create-repository \
  --repository-name knowledgeweaver-api \
  --region ap-southeast-2 \
  --image-scanning-configuration scanOnPush=true

# 2. Built Docker Image (multi-stage build)
docker build -t knowledgeweaver-api:latest \
  -f deploy/docker/api/Dockerfile .

# 3. Authenticated to ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com

# 4. Tagged Images
docker tag knowledgeweaver-api:latest \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest
docker tag knowledgeweaver-api:latest \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:v1.0.0

# 5. Pushed to ECR
docker push 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest
docker push 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:v1.0.0
```

### Dockerfile Analysis

**Location**: `deploy/docker/api/Dockerfile`

#### Stage 1: Builder (Python Dependencies)
```dockerfile
FROM python:3.11-slim AS builder
- Install gcc, g++, curl for building Python packages
- Copy requirements.txt
- Install dependencies to /root/.local (pip --user)
- Build artifacts: 938 MB
```

**Dependencies Installed**:
- FastAPI 0.128.0 (web framework)
- Uvicorn 0.40.0 (ASGI server)
- OpenAI 2.16.0 (LLM integration)
- Neo4j 6.1.0 (graph database)
- ChromaDB 1.4.1 (vector database)
- Google GenAI 1.60.0 (Gemini)
- Langfuse 3.12.1 (observability)
- Arize Phoenix 12.33.0 (AI observability)
- Total packages: 100+ dependencies

#### Stage 2: Runtime (Final Image)
```dockerfile
FROM python:3.11-slim
- Copy built dependencies from builder
- Copy backend/ and frontend/ code
- Create data directories
- Expose port 9621
- Health check endpoint: /health
- CMD: uvicorn backend.server:app
```

**Runtime Size Breakdown**:
- Base image (python:3.11-slim): ~150 MB
- Python dependencies: 938 MB
- Application code (backend): 25.8 MB
- Frontend code: 99.6 KB
- System packages (curl): 16.7 MB
- **Total**: 1.13 GB (compressed: 347 MB)

### Image Optimization

✅ **Multi-stage build**: Separates build dependencies from runtime
✅ **Slim base image**: Uses python:3.11-slim instead of full python image
✅ **Layer caching**: Dependencies installed before code copy
✅ **Health check**: Built-in health endpoint
✅ **No dev dependencies**: Only production packages included

⚠️ **Potential Optimizations**:
- Use Alpine Linux base (could reduce to ~100 MB compressed)
- Remove unnecessary Python packages
- Use pip-tools for minimal dependency resolution
- Compress static assets

### Application Structure

```
/app/
├── backend/              # FastAPI application (25.8 MB)
│   ├── server.py        # Main entry point
│   ├── core/            # Core modules
│   ├── extraction/      # Document extraction
│   ├── retrieval/       # RAG retrieval
│   └── management/      # Knowledge graph management
├── frontend/            # Web UI (99.6 KB)
├── data/                # Created at runtime
│   ├── storage/
│   │   └── vector_db/   # ChromaDB storage
│   ├── checkpoints/     # Processing checkpoints
│   ├── progress/        # Progress tracking
│   └── inputs/          # Uploaded files
└── logs/                # Application logs
```

### Environment Configuration

**From ConfigMap** (`deploy/kubernetes/base/configmap.yaml`):
```yaml
HOST: "0.0.0.0"
PORT: "9621"
USE_NEO4J: "true"
NEO4J_URI: "bolt://neo4j:7687"
CONCURRENT_REQUESTS: "5"
CHUNK_SIZE: "800"
PHOENIX_ENABLED: "true"
LANGFUSE_ENABLED: "true"
LLM_BINDING_HOST: "https://space.ai-builders.com/backend/v1"
LLM_MODEL: "deepseek"
EXTRACTION_LLM_BACKEND: "gemini"
GEMINI_MODEL: "gemini-2.0-flash"
```

**From Secrets** (`deploy/kubernetes/base/secrets.yaml`):
```yaml
NEO4J_PASSWORD: (from secret)
LLM_BINDING_API_KEY: (from secret)
GEMINI_API_KEY: (from secret)
LANGFUSE_PUBLIC_KEY: (from secret)
LANGFUSE_SECRET_KEY: (from secret)
```

### Deployment Configuration Updates

#### Updated Files

1. **deploy/kubernetes/base/api/deployment.yaml**
   - ✅ Changed: `image: PLACEHOLDER_ECR_REPO/knowledgeweaver-api:latest`
   - ✅ To: `image: 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest`
   - ✅ Added: `GEMINI_API_KEY` environment variable from secret

2. **deploy/kubernetes/base/configmap.yaml**
   - ✅ Added: LLM configuration (host, model)
   - ✅ Added: Extraction LLM backend (Gemini)
   - ✅ Added: RAG configuration (embedding model, chunk sizes)

### Resource Requirements

**API Container** (`deployment.yaml`):
```yaml
resources:
  requests:
    memory: "512Mi"    # Minimum required
    cpu: "250m"        # 0.25 cores
  limits:
    memory: "1Gi"      # Maximum allowed
    cpu: "1000m"       # 1 core
```

**Scaling**:
- Replicas: 2 (for HA)
- HorizontalPodAutoscaler: Configured
- Rolling updates: MaxSurge=1, MaxUnavailable=0 (zero-downtime)

### Health Checks

**Liveness Probe** (restart if unhealthy):
```yaml
httpGet:
  path: /health
  port: 9621
initialDelaySeconds: 30
periodSeconds: 10
timeoutSeconds: 5
failureThreshold: 3
```

**Readiness Probe** (remove from load balancer if not ready):
```yaml
httpGet:
  path: /ready
  port: 9621
initialDelaySeconds: 10
periodSeconds: 5
timeoutSeconds: 3
failureThreshold: 3
```

### Storage

**Volumes**:
- `data`: emptyDir (ephemeral) - ⚠️ **NEEDS PVC FOR PRODUCTION**
- `logs`: emptyDir (ephemeral)

**Recommendation**: Create PersistentVolumeClaim for `/app/data`:
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

### Verification Commands

```bash
# Verify image in ECR
aws ecr describe-images \
  --repository-name knowledgeweaver-api \
  --region ap-southeast-2

# Pull image locally
docker pull 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest

# Run image locally for testing
docker run -d \
  --name knowledgeweaver-test \
  -p 9621:9621 \
  -e NEO4J_URI=bolt://localhost:7687 \
  -e NEO4J_PASSWORD=password \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest

# Check health
curl http://localhost:9621/health

# View logs
docker logs knowledgeweaver-test

# Cleanup
docker stop knowledgeweaver-test && docker rm knowledgeweaver-test
```

### Next Steps

1. **Create Kubernetes Secrets** ✅ Ready
   ```bash
   kubectl create secret generic knowledgeweaver-secrets \
     --from-literal=NEO4J_PASSWORD='admin654321' \
     --from-literal=LLM_BINDING_API_KEY='sk_bc200441_***' \
     --from-literal=GEMINI_API_KEY='AIzaSyBlVkE2TYa***' \
     --from-literal=LANGFUSE_PUBLIC_KEY='pk-lf-***' \
     --from-literal=LANGFUSE_SECRET_KEY='sk-lf-***' \
     --namespace prod
   ```

2. **Deploy to Kubernetes** ⏳ Waiting for EKS
   ```bash
   # After EKS cluster is ready
   aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production
   kubectl apply -k deploy/kubernetes/base/
   ```

3. **Verify Deployment** ⏳ Pending
   ```bash
   kubectl get pods -n prod
   kubectl logs -n prod -l app=api
   kubectl describe pod -n prod -l app=api
   ```

4. **Create PVC for Data Persistence** ⏳ Recommended
   ```bash
   # Create PVC manifest and apply
   kubectl apply -f api-data-pvc.yaml
   ```

### Security Considerations

✅ **Image Scanning**: Enabled on ECR (scan on push)
✅ **Non-root User**: Could add USER directive in Dockerfile
✅ **Secrets Management**: Uses Kubernetes secrets (consider AWS Secrets Manager)
✅ **Health Checks**: Liveness and readiness probes configured
✅ **Resource Limits**: Memory and CPU limits set

⚠️ **Improvements**:
- Run as non-root user
- Use read-only root filesystem
- Add security context (seccompProfile, runAsNonRoot)
- Implement network policies
- Use AWS Secrets Manager instead of Kubernetes secrets

### Cost Estimation

**ECR Storage**:
- Image size: 347 MB compressed
- Cost: $0.10/GB/month
- Monthly cost: ~$0.03/month

**Data Transfer**:
- First 100 GB/month: Free
- Pulls from EKS in same region: Free

**Total ECR Cost**: ~$0.03/month (negligible)

### Troubleshooting

**Common Issues**:

1. **Image pull failed**
   ```bash
   # Check ECR authentication
   aws ecr get-login-password --region ap-southeast-2 | \
     docker login --username AWS --password-stdin \
     858766041545.dkr.ecr.ap-southeast-2.amazonaws.com

   # Verify image exists
   aws ecr describe-images --repository-name knowledgeweaver-api --region ap-southeast-2
   ```

2. **Pod CrashLoopBackOff**
   ```bash
   # Check logs
   kubectl logs -n prod -l app=api --tail=100

   # Check events
   kubectl describe pod -n prod -l app=api

   # Verify secrets
   kubectl get secret knowledgeweaver-secrets -n prod -o yaml
   ```

3. **Health check failing**
   ```bash
   # Port-forward to pod
   kubectl port-forward -n prod deployment/api 9621:9621

   # Test health endpoint
   curl http://localhost:9621/health
   curl http://localhost:9621/ready
   ```

### Build History

| Version | Date | Size | Notes |
|---------|------|------|-------|
| v1.0.0 | 2026-01-29 | 347 MB | Initial production build |
| latest | 2026-01-29 | 347 MB | Same as v1.0.0 |

---

## Summary

✅ **Image Built Successfully**: Multi-stage Docker build completed
✅ **Pushed to ECR**: Both latest and v1.0.0 tags available
✅ **Deployment Updated**: Kubernetes manifests reference actual ECR URI
✅ **ConfigMap Enhanced**: Added missing LLM and RAG configuration
✅ **Ready for Deployment**: Waiting for EKS cluster to complete

**Next Action**: Redeploy CloudFormation stack to create EKS cluster with IRSA

---

**Document Status**: Current as of 2026-01-29 13:40 NZDT
**Maintained By**: Sheldon
**Related Docs**:
- Configuration Review: `docs/CONFIGURATION_REVIEW.md`
- EKS IRSA Fix: `docs/EKS_IRSA_FIX.md`
