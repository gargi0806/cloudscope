# Local validation evidence — 28 October 2026

**Passed in the provided build workspace**

- `python -m pytest -q tests`: **5 passed**.
- `python scripts/validate_manifests.py`: checked ten Kubernetes YAML manifests for parseability and selected workload security properties.
- `bash -n scripts/deploy-eks.sh scripts/local-kind.sh scripts/push-ecr.sh`: passed script syntax check.
- `TestClient(app).get('/api/v1/status')`: HTTP 200 and real local runtime fields.
- YAML parsing of GitHub workflows and Dependabot configuration completed.

**Not available for execution here; verify yourself before making deployment claims**

- Docker image build/run and real `kind` cluster: Docker/kind binaries unavailable in the build workspace.
- Terraform `init`, `fmt`, `validate`, `plan` or `apply`: Terraform CLI unavailable, and no AWS account connected for deployment.
- Real GitHub Actions, AWS ECR push, EKS rollout, ingress or load testing: not run.
- Cloud costs and AWS Budget notifications: not measured or created.

This is source code plus local automated test evidence, **not proof of AWS deployment**.
