# Cost controls and cleanup

## What bills even if nobody visits the dashboard?

- **EKS cluster control plane:** AWS currently lists `$0.10/cluster-hour` while running a standard-support Kubernetes version, and `$0.60/cluster-hour` on extended support. See https://aws.amazon.com/eks/pricing/ .
- **Managed EC2 worker instances:** charged while running (default 2 x `t3.medium` on-demand) plus EBS storage.
- **NAT gateway:** incurs an hourly charge **plus processing/data charges** even if traffic is low.
- **Network/public IP, CloudWatch logs, ECR storage/scans and optional ALB** can add costs.
- Prices depend on region, terms, hours and transfer. Check the AWS Pricing Calculator for ap-south-1 or your chosen region **before** `terraform apply`. Do not rely on the $35 alert threshold as an estimate.

## Guardrails in the code

- Hard limit of 1-3 EC2 worker nodes through Terraform validation.
- No application LoadBalancer or public ingress enabled by default.
- ECR lifecycle keeps only the ten newest images.
- CloudWatch EKS logs retained for seven days.
- Explicit resource tags for ownership and review.
- AWS Budget notification at 80% actual and 100% forecasted of a monthly **account-wide** budget. It is an alert, **not** an automatic shutdown, ceiling, or a project-only budget.
- All AWS provisioning is an explicit local `terraform apply`, never CI automatic.

## Budget-first routine

1. Work locally with `kind` until screenshots, tests and manifests look complete.
2. If you choose a cloud demo, determine a short, fixed time window and a spending limit you can afford. Set budget alerts in the AWS console before provisioning; alerts can lag actual spending.
3. Review `terraform plan` and the AWS Pricing Calculator. Avoid deploying optional ALB.
4. Provision, collect evidence, then `terraform destroy` **the same day** when the demo is finished.
5. Check EKS, EC2, NAT gateways, EIPs, EBS, Load Balancers, ECR and Cost Explorer after cleanup. The ECR repository (including build images) is not force-deleted: remove images first or clear it deliberately if `destroy` reports a non-empty repository.
6. Verify there are no residual public IPs, snapshots, load balancers or other billable resources. A Budget alert is not a guarantee of spend control.

## Teardown commands

```bash
cd terraform
terraform plan -destroy
terraform destroy
```

Do **not** delete Terraform state or blindly delete resources. If destruction fails, inspect the error and reconcile it. Work only in a dedicated learning AWS account when possible. IAM OIDC provider may be account-shared; don't destroy shared identity resources that predated your project.
