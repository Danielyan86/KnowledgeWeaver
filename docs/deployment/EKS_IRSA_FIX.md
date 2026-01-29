# EKS IRSA Fix - Deployment History

## Issue Summary

**Date**: 2026-01-29
**Problem**: CloudFormation deployment failed with `ROLLBACK_FAILED` status

### Root Cause

The EBS CSI Driver addon failed to start with error:
```
failed to refresh cached credentials, no EC2 IMDS role found
CrashLoopBackOff: 2/4 pods available
```

**Why it failed:**
- The EBS CSI Driver addon was deployed without IRSA (IAM Roles for Service Accounts)
- The addon tried to use node IAM role permissions, but CSI driver pods cannot access EC2 IMDS
- Without proper IAM credentials, the driver pods crashed in a loop

## Solution Applied

### Changes to `deploy/cloudformation/templates/eks.yaml`

#### 1. Removed EBS Policy from Node Role
**Before** (Line 120):
```yaml
ManagedPolicyArns:
  - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
  - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
  - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
  - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy  # ❌ Removed
```

**After**:
```yaml
ManagedPolicyArns:
  - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
  - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
  - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
  - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

**Reason**: Node role should not have EBS permissions; use dedicated service account role instead.

#### 2. Added OIDC Identity Provider
```yaml
OIDCProvider:
  Type: AWS::IAM::OIDCProvider
  Properties:
    Url: !GetAtt EKSCluster.OpenIdConnectIssuerUrl
    ClientIdList:
      - sts.amazonaws.com
    ThumbprintList:
      - 9e99a48a9960b14926bb7f3b02e22da2b0ab7280
```

**Purpose**: Enables IRSA by allowing Kubernetes service accounts to assume IAM roles.

#### 3. Added EBS CSI Driver IAM Role
```yaml
EBSCSIDriverRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: !Sub '${ProjectName}-${Environment}-ebs-csi-driver-role'
    AssumeRolePolicyDocument:
      Fn::Sub:
        - |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Federated": "${OIDCProviderArn}"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                  "StringEquals": {
                    "${OIDCUrl}:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
                    "${OIDCUrl}:aud": "sts.amazonaws.com"
                  }
                }
              }
            ]
          }
        - OIDCProviderArn: !GetAtt OIDCProvider.Arn
          OIDCUrl: !GetAtt EKSCluster.OpenIdConnectIssuerUrl
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
```

**Purpose**:
- Dedicated IAM role for EBS CSI driver service account
- Trust policy allows only the `ebs-csi-controller-sa` service account in `kube-system` namespace
- Follows least privilege principle

#### 4. Updated EBS CSI Driver Addon
**Before**:
```yaml
EBSCSIDriverAddon:
  Type: AWS::EKS::Addon
  DependsOn: NodeGroup
  Properties:
    ClusterName: !Ref EKSCluster
    AddonName: aws-ebs-csi-driver
    # ServiceAccountRoleArn will be added after OIDC Provider setup
```

**After**:
```yaml
EBSCSIDriverAddon:
  Type: AWS::EKS::Addon
  DependsOn:
    - NodeGroup
    - EBSCSIDriverRole
  Properties:
    ClusterName: !Ref EKSCluster
    AddonName: aws-ebs-csi-driver
    ServiceAccountRoleArn: !GetAtt EBSCSIDriverRole.Arn
    ResolveConflicts: OVERWRITE
```

**Changes**:
- Added `EBSCSIDriverRole` to dependencies
- Added `ServiceAccountRoleArn` pointing to the dedicated IAM role
- Added `ResolveConflicts: OVERWRITE` for safer updates

#### 5. Added New Outputs
```yaml
OIDCProviderArn:
  Description: OIDC Provider ARN for creating additional IRSA roles
  Value: !GetAtt OIDCProvider.Arn
  Export:
    Name: !Sub '${AWS::StackName}-OIDCProviderArn'

EBSCSIDriverRoleArn:
  Description: IAM Role ARN for EBS CSI Driver
  Value: !GetAtt EBSCSIDriverRole.Arn
  Export:
    Name: !Sub '${AWS::StackName}-EBSCSIDriverRoleArn'
```

**Purpose**: Makes it easy to create additional IRSA roles for other services (ALB controller, external-dns, etc.)

## Security Benefits

### Before (Node IAM Role)
❌ **Over-permissioned**: Every pod on the node inherits EBS permissions
❌ **No isolation**: Cannot restrict which pods can manage EBS volumes
❌ **Static credentials**: Uses EC2 instance profile credentials
❌ **Doesn't work**: CSI driver pods can't access IMDS anyway

### After (IRSA)
✅ **Least privilege**: Only `ebs-csi-controller-sa` can access EBS APIs
✅ **Namespace isolation**: Trust policy restricts to `kube-system` namespace
✅ **Temporary credentials**: Tokens expire every 15 minutes and auto-refresh
✅ **Auditable**: IAM CloudTrail logs show which service account made calls

## Deployment Timeline

| Time | Event |
|------|-------|
| 2026-01-28 20:45 | Initial deployment failed - EBS CSI Driver crash |
| 2026-01-28 20:46 | Stack rollback started |
| 2026-01-29 | Rollback failed - manual cleanup required |
| 2026-01-29 | Template fixed with IRSA configuration |
| 2026-01-29 | Stack deleted and redeployed with fixed template |

## Current Deployment Status

**Stack**: `knowledgeweaver-production`
**Status**: `CREATE_IN_PROGRESS` ✅

### Resource Status
- ✅ VPCStack: `CREATE_COMPLETE`
- ✅ S3Stack: `CREATE_COMPLETE`
- ✅ ECRStack: `CREATE_COMPLETE`
- 🔄 EKSStack: `CREATE_IN_PROGRESS`
  - ✅ EKSClusterRole: Created
  - ✅ NodeGroupRole: Created (without EBS policy)
  - 🔄 EKSCluster: Creating (~10-12 minutes)
  - ⏳ OIDCProvider: Pending (after cluster)
  - ⏳ EBSCSIDriverRole: Pending (after OIDC)
  - ⏳ NodeGroup: Pending
  - ⏳ EBSCSIDriverAddon: Pending (final step)

**Expected completion**: 15-20 minutes from deployment start

## Future IRSA Examples

With OIDC provider in place, you can easily add more service account roles:

### AWS Load Balancer Controller
```yaml
ALBControllerRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Fn::Sub:
        - |
          {
            "Version": "2012-10-17",
            "Statement": [{
              "Effect": "Allow",
              "Principal": {"Federated": "${OIDCProviderArn}"},
              "Action": "sts:AssumeRoleWithWebIdentity",
              "Condition": {
                "StringEquals": {
                  "${OIDCUrl}:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller"
                }
              }
            }]
          }
        - OIDCProviderArn: !GetAtt OIDCProvider.Arn
          OIDCUrl: !GetAtt EKSCluster.OpenIdConnectIssuerUrl
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
```

### External DNS
```yaml
ExternalDNSRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      # Same pattern as above, different service account
      "${OIDCUrl}:sub": "system:serviceaccount:kube-system:external-dns"
    Policies:
      - PolicyName: Route53Access
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action: route53:ChangeResourceRecordSets
              Resource: "*"
```

## Verification Steps

Once deployment completes, verify IRSA is working:

```bash
# 1. Update kubeconfig
aws eks update-kubeconfig --region ap-southeast-2 --name knowledgeweaver-production

# 2. Check EBS CSI driver pods
kubectl get pods -n kube-system -l app=ebs-csi-controller

# 3. Verify service account annotation
kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml | grep eks.amazonaws.com/role-arn

# 4. Check pod environment variables
kubectl describe pod -n kube-system -l app=ebs-csi-controller | grep -A5 "Environment:"

# Should see:
# AWS_ROLE_ARN=arn:aws:iam::XXX:role/knowledgeweaver-production-ebs-csi-driver-role
# AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token

# 5. Test EBS volume creation
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 1Gi
EOF

kubectl get pvc test-ebs-claim
# Should show STATUS: Bound
```

## References

- [AWS EKS IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [EBS CSI Driver Documentation](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [AWS Best Practices for Security](https://aws.github.io/aws-eks-best-practices/security/docs/)

---

**Fixed by**: Sheldon
**Date**: 2026-01-29
**Stack ID**: arn:aws:cloudformation:ap-southeast-2:858766041545:stack/knowledgeweaver-production/e65178e0-fc8e-11f0-a3b2-02cb6c72aad9
