# KnowledgeWeaver - Quick Reference

## 🚀 Port-Forward Management (Single Script)

### Location
```bash
cd /Users/sheldon/Github/KnowledgeWeaver/deploy/scripts
```

### Commands
```bash
# Start all port-forwards
bash portforward.sh start

# Stop all port-forwards
bash portforward.sh stop

# Check status
bash portforward.sh status

# Restart all
bash portforward.sh restart
```

### Services Exposed

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:9621 | - |
| Langfuse | http://localhost:3000 | Create on first visit |
| Neo4j Browser | http://localhost:7474 | neo4j / admin654321 |
| Neo4j Bolt | bolt://localhost:7687 | neo4j / admin654321 |
| Phoenix | http://localhost:6006 | - |

---

## 🛠️ Build & Deploy Scripts

### Full Build & Deploy
Builds Docker image and deploys to Kubernetes.

```bash
cd deploy/scripts
bash build-and-deploy.sh
```

**What it does:**
- Builds Docker image for linux/amd64
- Pushes to ECR
- Updates Kubernetes resources
- Creates/updates secrets
- Restarts API deployment

### Quick Deploy (No Build)
Deploys using existing ECR image.

```bash
cd deploy/scripts
bash quick-deploy.sh
```

**What it does:**
- Applies Kubernetes manifests
- Restarts API deployment
- Much faster than full build

---

## 🐳 Docker Commands

### Build Locally
```bash
cd /Users/sheldon/Github/KnowledgeWeaver

# Build for amd64 (EKS nodes)
docker buildx build \
  --platform linux/amd64 \
  -t knowledgeweaver-api:local \
  -f deploy/docker/api/Dockerfile \
  .
```

### Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com

# Build and push
docker buildx build \
  --platform linux/amd64 \
  -t 858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest \
  -f deploy/docker/api/Dockerfile \
  . \
  --push
```

---

## ☸️ Kubernetes Commands

### View Resources
```bash
# All pods in demo namespace
kubectl get pods -n demo

# All services
kubectl get svc -n demo

# Pod details
kubectl describe pod <pod-name> -n demo

# Events
kubectl get events -n demo --sort-by='.lastTimestamp'
```

### View Logs
```bash
# API logs (follow)
kubectl logs -n demo deployment/api -f

# Neo4j logs
kubectl logs -n demo neo4j-0 -f

# Langfuse logs
kubectl logs -n demo deployment/langfuse -f

# Phoenix logs
kubectl logs -n demo deployment/phoenix -f

# All containers in a pod
kubectl logs -n demo <pod-name> --all-containers=true -f
```

### Restart Services
```bash
# Restart API
kubectl rollout restart deployment/api -n demo

# Restart Langfuse
kubectl rollout restart deployment/langfuse -n demo

# Restart Phoenix
kubectl rollout restart deployment/phoenix -n demo

# Delete and recreate Neo4j pod
kubectl delete pod neo4j-0 -n demo
```

### Resource Usage
```bash
# Pod resource usage
kubectl top pods -n demo

# Node resource usage
kubectl top nodes
```

### Execute Commands in Pods
```bash
# Shell into API pod
kubectl exec -it -n demo deployment/api -- /bin/bash

# Shell into Neo4j pod
kubectl exec -it -n demo neo4j-0 -- /bin/bash

# Run single command
kubectl exec -n demo deployment/api -- env
```

---

## 🗄️ Database Access

### Neo4j
```bash
# Via port-forward (after running portforward.sh start)
# Browser: http://localhost:7474
# Username: neo4j
# Password: admin654321

# Using cypher-shell (if installed)
cypher-shell -a bolt://localhost:7687 -u neo4j -p admin654321

# Example query
MATCH (n) RETURN count(n);
```

### PostgreSQL (Langfuse)
```bash
# Port-forward to postgres
kubectl port-forward -n demo postgres-0 5432:5432

# Connect using psql
psql -h localhost -p 5432 -U langfuse -d langfuse
# Password: From langfuse-secrets
```

---

## 🔐 Secrets Management

### View Secrets
```bash
# List secrets
kubectl get secrets -n demo

# View secret (base64 decoded)
kubectl get secret knowledgeweaver-secrets -n demo \
  -o jsonpath='{.data.NEO4J_PASSWORD}' | base64 -d
```

### Update Secrets
```bash
# Edit .env file
vim .env

# Recreate secrets
cd deploy/kubernetes/scripts
bash create-secrets.sh

# Restart services to pick up new secrets
kubectl rollout restart deployment/api -n demo
kubectl rollout restart deployment/langfuse -n demo
```

---

## 🔍 Troubleshooting

### Pod Stuck in Pending
```bash
# Check events
kubectl describe pod <pod-name> -n demo

# Common issues:
# - Insufficient resources
# - PVC not bound
# - Node selector issues
```

### Pod CrashLoopBackOff
```bash
# View logs
kubectl logs -n demo <pod-name>

# View previous logs (if restarted)
kubectl logs -n demo <pod-name> --previous

# Common issues:
# - Missing environment variables
# - Database connection failures
# - Application errors
```

### Image Pull Errors
```bash
# Check ECR images
aws ecr describe-images \
  --repository-name knowledgeweaver-api \
  --region ap-southeast-2

# Verify image exists
docker manifest inspect \
  858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api:latest
```

### Storage Issues
```bash
# Check PVCs
kubectl get pvc -n demo

# Check PVC details
kubectl describe pvc <pvc-name> -n demo

# Check storage classes
kubectl get storageclass
```

### Network Issues
```bash
# Test pod-to-pod connectivity
kubectl exec -n demo deployment/api -- curl http://neo4j:7474

# Test DNS resolution
kubectl exec -n demo deployment/api -- nslookup neo4j

# Check services
kubectl get svc -n demo
```

---

## 📊 Monitoring

### Check API Health
```bash
curl http://localhost:9621/health
curl http://localhost:9621/stats
```

### Check Cluster Health
```bash
# Cluster info
kubectl cluster-info

# Node status
kubectl get nodes

# Component status
kubectl get componentstatuses
```

### View Metrics
```bash
# Enable metrics-server (if not installed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View metrics
kubectl top nodes
kubectl top pods -n demo
```

---

## 🌐 AWS Commands

### EKS Cluster
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region ap-southeast-2 \
  --name knowledgeweaver-production

# Get cluster info
aws eks describe-cluster \
  --name knowledgeweaver-production \
  --region ap-southeast-2

# List node groups
aws eks list-nodegroups \
  --cluster-name knowledgeweaver-production \
  --region ap-southeast-2
```

### CloudFormation
```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2

# View stack events
aws cloudformation describe-stack-events \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2 \
  --max-items 20

# Delete stack (DANGER!)
aws cloudformation delete-stack \
  --stack-name knowledgeweaver-production \
  --region ap-southeast-2
```

---

## 🧪 Testing

### API Tests
```bash
# Health check
curl http://localhost:9621/health

# Get stats
curl http://localhost:9621/stats

# API docs (interactive)
open http://localhost:9621/docs
```

### Neo4j Tests
```bash
# Simple query
cypher-shell -a bolt://localhost:7687 -u neo4j -p admin654321 \
  "MATCH (n) RETURN count(n) as node_count;"

# Check database
cypher-shell -a bolt://localhost:7687 -u neo4j -p admin654321 \
  "CALL db.schema.visualization();"
```

---

## 📝 Useful Files

| File | Purpose |
|------|---------|
| `deploy/scripts/portforward.sh` | Port-forward management |
| `deploy/scripts/build-and-deploy.sh` | Full build & deploy |
| `deploy/scripts/quick-deploy.sh` | Quick redeploy |
| `deploy/kubernetes/scripts/create-secrets.sh` | Create K8s secrets |
| `DEPLOYMENT_STATUS.md` | Deployment status & notes |
| `QUICK_REFERENCE.md` | This file |
| `.env` | Environment variables |

---

## 🆘 Getting Help

### View Documentation
- Architecture: `/tmp/architecture-review.md`
- Deployment: `DEPLOYMENT_STATUS.md`
- This Reference: `QUICK_REFERENCE.md`

### Common Issues
See `DEPLOYMENT_STATUS.md` → Troubleshooting section

### Support
- GitHub Issues: [Create issue for problems]
- Documentation: Check `docs/` directory

---

**Last Updated:** 2026-01-29
**Cluster:** knowledgeweaver-production
**Region:** ap-southeast-2
**Namespace:** demo
