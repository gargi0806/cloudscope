#!/usr/bin/env bash
set -euo pipefail
for bin in docker kind kubectl; do command -v "$bin" >/dev/null || { echo "Install $bin first" >&2; exit 1; }; done
docker build -t cloudscope-pulse:dev .
kind get clusters | grep -qx cloudscope || kind create cluster --name cloudscope
kind load docker-image cloudscope-pulse:dev --name cloudscope
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -k k8s/overlays/local
# Restart pods to pick up a newly loaded local :dev image on repeated runs.
kubectl -n cloudscope rollout restart deployment/cloudscope-api
kubectl -n cloudscope rollout status deployment/cloudscope-api --timeout=180s
echo 'Open http://localhost:8080 after starting the port-forward below:'
echo 'kubectl -n cloudscope port-forward svc/cloudscope-api 8080:80'
