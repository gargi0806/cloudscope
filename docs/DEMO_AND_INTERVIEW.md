# Explain and demonstrate CloudScope

## Project title

**CloudScope: Serverless AWS Resource Audit and Cost Hygiene Platform**

## Problem and objective

Student and development AWS accounts can accumulate unattached storage, unassociated addresses, unclear ownership and outdated administration rules. Manual checks across consoles are repetitive and easy to miss. CloudScope collects inventory, evaluates five transparent rules and generates an actionable review report.

The objective is to demonstrate infrastructure automation, IAM boundaries, AWS API integration, failure handling, reporting and CI/CD. It identifies review candidates; it does not prove waste, calculate savings or change resources.

## Two-minute demonstration

1. **Problem — 20 seconds:** Explain the difficulty of checking resource ownership and forgotten resources across regions.
2. **Run — 20 seconds:** Execute `python -m cloudscope demo --out reports`. Point out that it is synthetic data and needs no AWS credentials.
3. **Evidence — 40 seconds:** Open the HTML report. Select High priority, expand the administration-rule recommendation, then filter Singapore to show its unattached volume. Explain why a permissive security group is not proof of actual public reachability.
4. **Cloud architecture — 25 seconds:** Explain EventBridge → Lambda, inventory reads, private S3 reports, SNS and failure monitoring.
5. **Engineering quality — 15 seconds:** Show the test run and explain that an API failure produces a partial scan rather than an empty “healthy” report.

If you later deploy to AWS, add a live invocation and show the private report. Until then, describe the Terraform deployment as provided but unverified in your account.

## Questions you should be able to answer

**Why Lambda?** The scheduled audit is intermittent and can finish without a continuously running server. Large accounts would need partitioned scans or an orchestrated workflow.

**Why Terraform?** It records the resource relationships, permissions, storage controls, scheduler and alarms in version-controlled configuration.

**Where is least privilege applied?** The scanner has four EC2 Describe actions constrained to configured regions. S3 writes target only the report prefix. SNS and SQS actions target specific resources. EC2 Describe actions use `Resource: "*"` because these inventory APIs do not support resource-level scoping.

**Why no automatic cleanup?** An unattached disk can contain important data, and an unassociated IP can be reserved for recovery. Deletion requires ownership and business-context review.

**How do you avoid missing resources?** The collector uses the SDK paginator for supported Describe calls, flattens instance reservations and scans each requested region. A failed later page keeps earlier results but marks the whole report partial.

**What is tested without AWS?** Pure rule logic, SDK request/response contracts with Stubber, pagination, errors, report encoding, CLI exit codes and Lambda storage/notification behavior with mocks. These are not substitutes for an end-to-end AWS deployment.

**How are dependencies packaged?** The build script installs the pinned SDK dependency set into a temporary directory alongside the application and ZIPs its contents at the deployment-package root.

**What does CI/CD mean here?** CI tests, packages and validates. The optional manual CD workflow assumes a restricted AWS role through OIDC and updates the existing Lambda. Initial infrastructure provisioning uses Terraform.

**What would you add next?** Time-limited suppressions, finding history/deduplication, per-region jobs, more complete network exposure checks and utilization data before making cost claims.

## Evidence to collect after your own deployment

- A successful Terraform plan/apply and the provider lock file.
- A successful manual Lambda result and a private report.
- A CloudWatch log entry and confirmed alert subscription.
- A successful GitHub CI run and, if configured, a manual deployment run.
- A cleanup demonstration in the dedicated sandbox.

Keep public screenshots synthetic or redact account IDs, addresses, resource names and personal information. Never claim measured savings, production use or completed deployment without your own evidence.
