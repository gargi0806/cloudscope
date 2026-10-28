# Security posture and explicit limitations

## Implemented

1. **Identity:** GitHub OIDC short-lived AWS sessions with exact repository + `main` branch trust condition. No stored access keys in workflows. A separate admin principal is required for initial namespace bootstrap.
2. **Least privilege:** ECR repo-scoped push IAM, EKS `DescribeCluster` read, namespace-scoped `AmazonEKSEditPolicy` via access entries. OIDC credentials do not have cluster-admin.
3. **Networking:** private worker subnets; one NAT for outbound traffic; EKS API public endpoint limited to supplied trusted CIDRs and private endpoint enabled. No internet-facing app load balancer by default.
4. **Workload:** non-root UID 10001, `readOnlyRootFilesystem`, disallowed privilege escalation, dropped Linux capabilities, runtime default seccomp, service account token disabled.
5. **Supply chain:** immutable commit SHA tags in ECR, ECR scan on push, weekly Dependabot, unit tests, dependency audit, Trivy scans on CI. CI image vulnerability scans are configured to fail on high/critical issues; update dependencies/base images when findings occur.
6. **Operational:** audit/authenticator/api logs with 7-day retention, health probes, rolling deployment, 2 replicas, resource limits, PodDisruptionBudget.
7. **Pod security:** namespace explicitly applies `restricted` Pod Security Admission labels.

## Not claimed (future hardening)

- No automatic network-policy **enforcement**. The AWS VPC CNI requires explicit network policy support configuration; merely writing `NetworkPolicy` YAML does not activate enforcement.
- No runtime WAF, managed TLS, SIEM, secrets manager, automated incident management, multi-region DR or formal SLO. Optional ALB requires a valid ACM certificate, controller and DNS.
- GitHub Action dependencies use tagged releases rather than immutable full SHAs; pin verified SHAs before a security-sensitive production release.
- Docker base image uses a moving `python:3.12-slim` tag; pin a reviewed OCI digest and generate an SBOM before a production release.
- Python dependency versions are pinned, but hash-locked dependencies are a next-step improvement.
- No automated IAM/key rotation because long-lived AWS keys are not used.
- The one shared NAT is not HA across AZs.
- No remote encrypted Terraform state is configured in this demo. Enable S3 remote state with locking, versioning, restricted IAM and encryption before teamwork.

## Threat model

Threats include supply-chain dependency vulnerabilities, malicious PR code, leaked tokens, exposed control plane, overprivileged CI, public ingress misconfiguration and runaway cloud costs. This project addresses some but not all; code review, branch protection, production environment protection, IAM policy review and live AWS validation remain necessary.

## GitHub branch and runner rules

Require PR reviews, protected `main`, restrict Actions write access, never attach a self-hosted deploy runner to jobs triggered from untrusted pull requests. The trusted deploy runner must have AWS CLI and kubectl, as well as network reachability to the restricted EKS API.
