#!/usr/bin/env bash
set -euo pipefail
: "${IMAGE:?Set IMAGE to the immutable ECR image URI including a commit SHA tag}"
: "${EKS_CLUSTER:?Set EKS_CLUSTER to the Terraform cluster name}"
: "${AWS_REGION:?Set AWS_REGION to your chosen AWS region}"
[[ "$IMAGE" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[a-z0-9._/-]+:[a-f0-9]{40}$ ]] || { echo "IMAGE must be an ECR URI tagged with a 40-character commit SHA" >&2; exit 1; }
command -v kubectl >/dev/null || { echo 'kubectl not found' >&2; exit 1; }
aws eks update-kubeconfig --name "$EKS_CLUSTER" --region "$AWS_REGION"
# Pre-create the cloudscope namespace once using an admin identity.
kubectl get namespace cloudscope >/dev/null || { echo 'Namespace cloudscope missing: bootstrap it with an EKS admin first.' >&2; exit 1; }
kubectl kustomize k8s/overlays/eks | sed "s|cloudscope-pulse:dev|${IMAGE}|g" | kubectl apply -f -
kubectl -n cloudscope rollout status deployment/cloudscope-api --timeout=240s
kubectl -n cloudscope get deploy,svc,pods -l app.kubernetes.io/name=cloudscope-api
