# What to show recruiters — evidence-first, no fabricated outcomes

## Resume project entry (use only after actually completing each stage)

**CloudScope Pulse | AWS / Terraform / Docker / Kubernetes / GitHub Actions**

Designed and implemented an observable, containerized FastAPI service with health probes, Prometheus metrics and a live status dashboard; automated unit testing, dependency auditing, container scanning and Terraform validation with GitHub Actions. Built Terraform definitions for EKS-managed nodes, private subnets, ECR, IAM OIDC deployment roles, CloudWatch logs and cost alerts. **Only claim EKS deployment after personally applying and validating it in AWS.**

## Evidence checklist

- [ ] `pytest` passing screenshot with test count
- [ ] Local operations UI screenshot showing live uptime and revision
- [ ] Docker build and non-root user verification output
- [ ] `kind get clusters`, `kubectl get pods -o wide`, `kubectl rollout status` screenshot
- [ ] CI green run (tests, Terraform, Trivy) on real GitHub repository
- [ ] Terraform `fmt`, `validate`, sanitized `plan` proof (no account IDs or IPs)
- [ ] **Only after deployment:** EKS nodes, ECR SHA image, private subnet mapping, rollout and cost dashboard evidence
- [ ] Before/after optimization evidence if cost changes are measured; do not invent percentages
- [ ] Teardown completion proof and cost review

## Interview talking points

1. Why is an immutable image tag safer than `latest`?
2. Why private nodes but a public (CIDR-restricted) control-plane endpoint?
3. Why use OIDC instead of storing IAM access keys in GitHub secrets?
4. What is the cost of an idle EKS control plane and why does `kind` help?
5. How do readiness vs liveness probes influence Kubernetes routing and restarts?
6. Why does an app with no persistent state simplify rolling deployment?
7. What fails when ECR image pulls cannot reach the network?
8. What is the RTO/rollback strategy when a deployment is bad?
9. Why does a budget alert not cap spend?
10. What is the single-AZ NAT tradeoff?

## Honest project status terminology

`Implemented locally` != `Deployed on EKS`. `Workflow configured` != `Workflow executed`. `Terraform authored` != `AWS infrastructure successfully provisioned`. Record demonstrated proof separately.
