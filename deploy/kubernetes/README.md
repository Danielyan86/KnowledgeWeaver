# Kubernetes Demo Deployment

This is a simplified Kubernetes configuration for **demo/interview purposes**.

## Configuration Summary

### Environment
- **Namespace**: `demo` (single environment)
- **API Replicas**: 1 (auto-scales 1-3)
- **Resource Limits**: 512Mi-1Gi memory, 250m-1000m CPU

### Components
- API (FastAPI backend)
- Neo4j (graph database)
- Phoenix (observability - optional)
- Langfuse (observability - optional)
- PostgreSQL (for observability tools)

## Quick Deploy

### 1. Create Namespace
```bash
kubectl apply -f base/namespace.yaml
```

### 2. Create Secrets
Edit `base/secrets.yaml` and add your credentials, then:
```bash
kubectl apply -f base/secrets.yaml
```

### 3. Deploy All Components
```bash
kubectl apply -f base/configmap.yaml
kubectl apply -f base/neo4j/
kubectl apply -f base/api/
# Optional: observability tools
kubectl apply -f base/observability/
```

### 4. Verify Deployment
```bash
kubectl get pods -n demo
kubectl get svc -n demo
```

## One-Command Deploy

```bash
# Deploy everything at once
kubectl apply -k base/
```

## Access the API

```bash
# Port forward to local machine
kubectl port-forward -n demo svc/api 9621:9621

# Or get the LoadBalancer/Ingress URL
kubectl get ingress -n demo
```

## Cleanup

```bash
kubectl delete namespace demo
```

## Notes

- This is a **demo configuration** - not production-ready
- No persistent volumes for simplicity (data will be lost on pod restart)
- No advanced security configurations
- Minimal resource requests for cost savings
- Single replica for simplicity

For production deployment, consider:
- Multi-replica setup
- Persistent volumes
- Resource quotas
- Network policies
- RBAC policies
- Ingress with TLS
