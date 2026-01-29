# Port Forward Management Scripts

Scripts to easily access KnowledgeWeaver services running on Kubernetes.

## Quick Start

```bash
# Start all port-forwards
cd deploy/scripts
bash start-portforward.sh

# Check status
bash status-portforward.sh

# Stop all port-forwards
bash stop-portforward.sh
```

## Available Scripts

### 1. start-portforward.sh
Starts port-forwards for all services and opens browsers.

**Services exposed:**
- API: http://localhost:9621
- Langfuse: http://localhost:3000
- Neo4j Browser: http://localhost:7474
- Neo4j Bolt: bolt://localhost:7687
- Phoenix: http://localhost:6006

**Usage:**
```bash
bash start-portforward.sh
```

**What it does:**
- Starts all port-forward processes in background
- Saves PIDs to `/tmp/knowledgeweaver-portforward.pid`
- Tests API health
- Opens browsers automatically (macOS only)

### 2. stop-portforward.sh
Stops all port-forward processes.

**Usage:**
```bash
bash stop-portforward.sh
```

**What it does:**
- Reads PIDs from PID file
- Kills all port-forward processes
- Cleans up PID file
- Falls back to killing all `kubectl port-forward` if PID file missing

### 3. status-portforward.sh
Shows status of port-forward processes and tests connectivity.

**Usage:**
```bash
bash status-portforward.sh
```

**What it shows:**
- Active port-forward processes from PID file
- All kubectl port-forward processes on system
- Connectivity test for each service

### 4. build-and-deploy.sh
Full build and deployment pipeline.

**Usage:**
```bash
bash build-and-deploy.sh
```

**What it does:**
- Builds Docker image for linux/amd64
- Pushes to ECR
- Updates Kubernetes manifests
- Creates/updates secrets
- Deploys all services
- Restarts API deployment

### 5. quick-deploy.sh
Quick deployment without building Docker image.

**Usage:**
```bash
bash quick-deploy.sh
```

**What it does:**
- Uses existing ECR image
- Deploys Kubernetes manifests
- Restarts API deployment

## Common Workflows

### Initial Setup
```bash
# Deploy infrastructure (first time)
cd deploy/cloudformation/scripts
bash deploy.sh

# Wait for completion (~15-20 minutes)

# Build and deploy application
cd ../../scripts
bash build-and-deploy.sh

# Start port-forwards
bash start-portforward.sh
```

### Daily Development
```bash
# Make code changes...

# Quick redeploy
cd deploy/scripts
bash build-and-deploy.sh

# Access services (if not already running)
bash start-portforward.sh
```

### Testing Services Locally
```bash
# Start port-forwards
bash start-portforward.sh

# Test API
curl http://localhost:9621/health
curl http://localhost:9621/stats

# Test Neo4j
# Connect with: bolt://localhost:7687
# Username: neo4j
# Password: admin654321

# View Langfuse
# Open: http://localhost:3000

# View Phoenix
# Open: http://localhost:6006
```

### Cleanup
```bash
# Stop port-forwards
bash stop-portforward.sh

# Or delete entire infrastructure
cd deploy/cloudformation/scripts
aws cloudformation delete-stack --stack-name knowledgeweaver-production --region ap-southeast-2
```

## Troubleshooting

### Port-forwards won't start
```bash
# Check if ports are already in use
lsof -i :9621
lsof -i :3000
lsof -i :7474
lsof -i :7687
lsof -i :6006

# Kill processes using those ports
kill -9 <PID>

# Or stop all kubectl port-forwards
pkill -f "kubectl port-forward"
```

### Can't connect to services
```bash
# Check pod status
kubectl get pods -n demo

# Check if port-forwards are running
bash status-portforward.sh

# View pod logs
kubectl logs -n demo deployment/api -f
kubectl logs -n demo neo4j-0 -f
kubectl logs -n demo deployment/langfuse -f
```

### Services not responding
```bash
# Restart failed pods
kubectl rollout restart deployment/api -n demo
kubectl rollout restart deployment/langfuse -n demo
kubectl delete pod neo4j-0 -n demo  # StatefulSet will recreate

# Check events
kubectl get events -n demo --sort-by='.lastTimestamp'
```

## Environment Variables

Scripts read configuration from:
- Namespace: `demo`
- AWS Region: `ap-southeast-2`
- Cluster: `knowledgeweaver-production`
- ECR Repo: `858766041545.dkr.ecr.ap-southeast-2.amazonaws.com/knowledgeweaver-api`

## PID File Location

Port-forward PIDs are saved to: `/tmp/knowledgeweaver-portforward.pid`

This allows the stop script to cleanly terminate all processes.

## macOS vs Linux

### macOS
- Uses `open` command to open browsers
- All features work out of the box

### Linux
- Replace `open` with `xdg-open` in start script
- Or comment out browser opening lines

## Security Notes

- Port-forwards expose services only on localhost
- No external access unless you explicitly allow it
- Services use Kubernetes secrets for credentials
- Neo4j password: Set in secrets (default: admin654321)

## License

MIT
