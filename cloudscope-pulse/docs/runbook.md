# Day-2 operations runbook

## Normal health check

```bash
kubectl -n cloudscope get deploy,svc,pods
kubectl -n cloudscope rollout status deployment/cloudscope-api
kubectl -n cloudscope port-forward svc/cloudscope-api 8080:80
curl -fsS http://localhost:8080/health/ready
curl -fsS http://localhost:8080/api/v1/status
```

## Pod restart or crash

```bash
kubectl -n cloudscope describe pod -l app.kubernetes.io/name=cloudscope-api
kubectl -n cloudscope logs deployment/cloudscope-api --all-containers --tail=100
kubectl -n cloudscope get events --sort-by=.lastTimestamp
```

## Image pull failure

Check that the tag exists in ECR, node IAM can pull from ECR, private nodes reach ECR via NAT/VPC endpoints, the region and account match, and the deployment image matches the pushed 40-character commit SHA.

## Pending pods

Check `kubectl describe` events, available node CPU/memory, cluster add-ons, scheduling constraints, and EC2 node group health. A 1-node low-cost demo is not HA.

## Rollback

```bash
kubectl -n cloudscope rollout history deployment/cloudscope-api
kubectl -n cloudscope rollout undo deployment/cloudscope-api
kubectl -n cloudscope rollout status deployment/cloudscope-api
```

For traceability, record the previous known-good ECR commit image and prefer explicit `kubectl set image` to it. Do not depend on old ReplicaSets after long retention windows.

## Alarm and cost incident

Budget emails are notifications, not spend stops. Investigate Cost Explorer and terminate unneeded resources via Terraform after confirming ownership.

## Optional HPA and public ingress

HPA needs metrics-server; run `kubectl apply -f k8s/optional/hpa.yaml` only after validating installation. Public HTTPS requires AWS Load Balancer Controller IAM/helm installation, ACM certificate, DNS, and replacement of placeholders in `k8s/optional/aws-alb-ingress.yaml` before applying. These are extra billable services.
