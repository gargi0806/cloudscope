# Your cloud project: CloudScope

**AWS Resource Audit & Cost Hygiene Platform**

A portfolio project for Gargi Verma, B.Tech CSE — Cloud Computing.

CloudScope checks an AWS account for overlooked resources, missing ownership tags and selected risky configurations. It generates a report with evidence and review suggestions. It never deletes, stops or changes the resources it scans.

## See the working demo now

1. Extract the ZIP completely.
2. Open `cloudscope/examples/demo-report/report.html` in Chrome or Edge.
3. Try the priority filter, region filter, resource search and “Recommended review” sections.

The supplied report uses **synthetic data**: 11 resources across two regions, producing 7 findings. It does not represent your AWS account.

## Run the project on Windows

Install Python 3.12 or newer if needed. Open a terminal inside the extracted `cloudscope` folder:

```powershell
py -m cloudscope demo --out reports
Start-Process reports/report.html
```

The demo needs no AWS account, login, paid service or additional Python packages. On macOS/Linux, use `python3` instead of `py` and open the report in your browser.

## What you have

| Component | What it does |
|---|---|
| Python + Boto3 | Collects AWS inventory and evaluates five audit rules |
| HTML / JSON / CSV | Human-readable dashboard and machine-readable results |
| Terraform | Defines Lambda, private S3, IAM, EventBridge, SNS, SQS and monitoring |
| Docker | Runs the same scanner in a non-root container |
| GitHub Actions | Tests, builds and validates; optional manual Lambda code delivery through OIDC |
| Automated tests | Covers rule edge cases, pagination, partial failures and report safety |
| Packaged Lambda | `dist/cloudscope-lambda.zip` contains the application and its SDK dependencies |

## Next steps

1. Read `README.md` to understand the five rules and architecture.
2. Read `docs/DEPLOYMENT.md` before connecting an AWS account. Real AWS usage can incur charges.
3. Follow `docs/DEMO_AND_INTERVIEW.md` to explain and demonstrate the project.
4. Check `docs/VALIDATION.md` for exactly what was tested and what still requires an AWS environment.

**Current status:** the local demo works. AWS infrastructure has not been deployed. Terraform provider validation and the Docker build are included in CI and still need to run in an environment with those tools.
