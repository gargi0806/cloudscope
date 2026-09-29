# Deploy CloudScope to AWS

The offline demo is ready to use. The steps below create real AWS resources; they have not been executed against an AWS account for this delivery.

## 1. Prepare

Use Python 3.12, AWS CLI v2, Terraform 1.6+ (the CI example uses 1.12.2) and a dedicated AWS sandbox account/profile. Docker is optional. The Terraform configuration targets standard commercial AWS regions.

Authenticate with an existing SSO/profile setup. For example, if your configured profile is named `cloudscope`:

```bash
aws sso login --profile cloudscope
aws sts get-caller-identity --profile cloudscope
```

The Terraform operator needs permission to manage the project's IAM role/policy, Lambda, S3, EventBridge, SNS, SQS and CloudWatch resources, including passing the scanner role to Lambda. The small scanner policy in `examples/scanner-policy.json` is only for inventory scans; it is not a Terraform provisioning policy. Use your organization's approved sandbox provisioning role.

Set the profile for the shell where you run Terraform:

```powershell
# Windows PowerShell
$env:AWS_PROFILE = "cloudscope"
```

```bash
# macOS/Linux
export AWS_PROFILE=cloudscope
```

Use the account identity output to verify the target. CloudScope performs inventory reads; Terraform itself creates resources. No credentials should be placed in Python, tfvars, GitHub source files or Docker images.

## 2. Build and test

From the project root:

```bash
python -m pip install -r requirements.lock
python -m unittest discover -s tests -v
python scripts/build_lambda.py
```

On Windows, replace `python` with `py` if needed. A built ZIP is supplied in `dist/`; rebuild it after changing application code or dependency versions. The build includes Boto3 and its dependencies instead of relying on the SDK version bundled with Lambda.

## 3. Configure Terraform

Copy `infra/terraform.tfvars.example` to `infra/terraform.tfvars` using your file manager, then edit it. Start with:

```hcl
aws_region       = "ap-south-1"
scan_regions     = ["ap-south-1"]
project_name     = "cloudscope"
owner            = "gargi-verma"
alert_email      = ""
schedule_enabled = false
```

`alert_email` is optional. Supply an address you control if you want alerts, then confirm the SNS subscription email after deployment. Without a confirmed subscriber, the topic exists but no email arrives. The project name must be unique for this project in your account; do not deploy two copies with the same role/function names.

Run:

```bash
terraform -chdir=infra fmt -recursive
terraform -chdir=infra init
terraform -chdir=infra validate
terraform -chdir=infra plan -out=cloudscope.tfplan
```

Inspect the plan before applying. This is the first provider-level validation step: the delivery environment could parse HCL but could not run Terraform or access the provider registry. If validation fails, resolve it before deploying.

The configuration initially uses local state. Keep `infra/terraform.tfstate` secure and backed up, and keep it out of Git. Commit the generated `.terraform.lock.hcl` provider lock file. For team use, configure a separately provisioned remote state backend with access controls and locking before deployment. Do not use the report bucket as a bootstrap state dependency.

```bash
terraform -chdir=infra apply cloudscope.tfplan
terraform -chdir=infra output
```

The report bucket name includes project, account and region. Public access is blocked. No website is published.

## 4. Run one manual scan

Use the `function_name` output (default `cloudscope-scanner`). The AWS CLI call below invokes synchronously:

```bash
aws lambda invoke --function-name cloudscope-scanner --region ap-south-1 --cli-binary-format raw-in-base64-out --payload '{}' response.json
```

Read both the CLI response metadata and `response.json`. A successful HTTP invocation does **not** prove the function succeeded: `FunctionError` in the CLI metadata indicates a failed invocation. A successful function result includes `status: complete`, resource counts and an `s3://.../report.html` URI.

Copy that exact URI into:

```bash
aws s3 cp s3://YOUR_REPORT_BUCKET/reports/DATE/RUN_ID/report.html ./report.html --region ap-south-1
```

Replace the example path with the actual URI. Open the downloaded file in your browser. Retrieve `report.json` from the same prefix for the full status and any collection errors. Your operator identity needs permission to read the report bucket; the scanner role intentionally does not have that permission.

Do not create deliberately vulnerable resources to test the scanner. The synthetic demo already exercises each rule. Existing resources in a sandbox can be reviewed without changing them.

## 5. Activate the daily schedule

After the manual scan succeeds, set `schedule_enabled = true` in `infra/terraform.tfvars`, then run `terraform plan` and `terraform apply` again. `rate(1 day)` is a recurring interval, not an 8 AM local-time schedule.

The EventBridge rule starts the Lambda asynchronously. EventBridge has two target-delivery retries; Lambda has one function retry. Both use the SQS failure queue for exhausted failures at their respective layers. Manual synchronous invocation does not use Lambda's asynchronous retry/DLQ path.

CloudWatch logs last 14 days. An Errors alarm detects failed invocations; a queue-depth alarm detects retained failure messages. SNS review alerts cover high-priority findings and partial scans. Medium/low-only results are saved without an application finding email. Reports and alerts can repeat because retries are not deduplicated.

For very large accounts, split work by region and add bounded concurrency/checkpoints instead of increasing the region list indefinitely. The initial function timeout is five minutes; each SDK call has its own retry and timeout budget.

## 6. Optional GitHub CI/CD

Upload the source project to a GitHub repository with a `main` branch. Ensure `.github/workflows` is included. Do not upload live reports, Terraform state, tfvars, credential files or build output. The supplied synthetic `examples/demo-report` is safe sample data. There is no Git remote configured in this package.

The CI workflow runs tests, builds the Lambda ZIP, validates Terraform and runs the Docker demo. CI does not need AWS credentials and does not apply infrastructure.

The optional `deploy-code.yml` workflow updates **only the already-created Lambda code**. It requires this one-time setup:

1. In IAM, use or create an OIDC provider for `https://token.actions.githubusercontent.com` with audience `sts.amazonaws.com`.
2. Create a deployment role named, for example, `cloudscope-github-deploy`. Replace `YOUR_ACCOUNT_ID` and `YOUR_OWNER/YOUR_REPO` in `examples/github-oidc-trust.json` with your actual values. Its subject is limited to that repository's `aws-demo` environment.
3. Attach `examples/github-deploy-policy.json` after replacing account, region and function name. It grants code update and configuration-read access to that one function.
4. In GitHub, create an environment named `aws-demo`. Restrict deployment branches to `main`, and configure a required reviewer where your GitHub plan supports it. Protect the branch and workflow files: code-deployment permission lets that workflow replace the function's code, which runs with the scanner role.
5. Add environment variables: `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION` and `AWS_LAMBDA_FUNCTION`.
6. Run “Deploy Lambda code (manual)” from Actions on `main`. It retests, packages, obtains short-lived OIDC credentials, updates the function, and waits for the update to finish.

This workflow does not change Terraform resources or manage Terraform state. After a code deployment, keep your checkout and local deployment ZIP aligned with the same commit before the next Terraform apply; otherwise Terraform may redeploy a different package. Lambda code update completion also does not prove the scan works—repeat the manual invocation check.

The workflow examples use version tags. For stricter supply-chain control, resolve the reviewed action versions to immutable commit SHAs before production use.

## Costs and cleanup

The demo runs locally without AWS. The deployed project can incur charges for Lambda, S3 requests/storage, CloudWatch logs/alarms, SNS, SQS and scheduling, depending on usage and your account's allowances. It does not create a NAT Gateway or an always-running compute instance. Set your own AWS Budget alert before experimenting. No fixed free-tier or monthly-cost promise is made.

To remove the deployed project:

1. Set `schedule_enabled = false` and apply that change.
2. Download reports you want to retain.
3. In S3, locate the exact report bucket from Terraform's output. Review and explicitly empty **all object versions and delete markers** for that bucket when you are ready to remove its reports.
4. Run `terraform -chdir=infra plan -destroy`, review the target resources, then `terraform -chdir=infra destroy`.

`force_destroy` is false, so Terraform will not automatically erase a nonempty report bucket. The auditor never deletes the EC2/EBS/IP resources it scanned. If you created a GitHub deployment role separately, remove it separately when it is no longer needed.

## Troubleshooting

| Symptom | Check |
|---|---|
| Demo works; live scan exits 2 | SDK installed, profile login current, STS identity, allowed regions and Describe permissions |
| Partial report | `errors` in JSON identifies the failed region/API; do not interpret absent findings as healthy |
| `NoSuchKey` downloading a report | Copy the exact successful run prefix; there is no mutable `latest` report |
| No SNS email | Subscription confirmed, topic policy, high-priority finding/partial status, and CloudWatch alarm state transitions |
| Timeout | CloudWatch logs, account inventory size and region count; split large scans |
| Lambda ZIP missing at plan | Run `python scripts/build_lambda.py` from the project root |
| Docker local output permission issue | Use the documented stopped-container `docker cp` flow instead of a host bind mount |
| Destroy fails on S3 | Retained versions/delete markers remain; review and empty only the intended report bucket |
