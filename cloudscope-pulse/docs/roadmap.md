# 10-day implementation roadmap

| Day | Deliverable | Evidence |
| --- | --- | --- |
| 1 | Understand API, run tests, launch local dashboard | `pytest`, browser screenshot |
| 2 | Dockerize and inspect non-root runtime | Docker build, curl response |
| 3 | Deploy to local `kind` and investigate pods | kubectl rollout proof |
| 4 | Make a real code change, commit and roll it out | Git history, healthy new revision |
| 5 | Push GitHub and make CI green | CI URL showing test, audit, image scan |
| 6 | Terraform fmt, validate, explain CIDR/NAT/IAM | validated configuration, diagram |
| 7 | Plan AWS in dedicated learning account, cost review | redacted Terraform plan |
| 8 | OPTIONAL short AWS EKS deployment after budget check | ECR, EKS and rollout proof |
| 9 | OPTIONAL deploy rollback and destroy | rollback record and destroy proof |
| 10 | README screenshots, demo walkthrough, resume bullet | polished public repo |

At every step: do not claim an optional AWS step unless completed. Spend zero AWS dollars if you stop after local kind/CI.
