# Validation record

Build prepared on 29 September 2026. These results describe this delivered source package, not an AWS production deployment.

GitHub Actions [run 36578857204](https://github.com/gargi0806/cloudscope/actions/runs/36578857204) completed successfully on 29 September 2026 for source commit `10f38f5c2aaef7ded7675f1eeaa33b2771b01bf9`. The desktop and mobile captures from its `cloudscope-build` artifact are preserved in [screenshots/](screenshots/README.md).

| Check | Result | Evidence / limitation |
|---|---|---|
| Python automated tests | **22 passed** | `python -m unittest discover -s tests -v` under Python 3.12.14; completed without failures or warnings on the final run |
| Offline CLI demo | **Passed** | 11 synthetic resources, 7 findings; 1 high, 4 medium, 2 low; all three reports generated |
| AWS SDK request/response handling | **Passed locally** | Real Boto3 clients with Stubber validate pagination, reservation flattening and failure continuation; no AWS network calls |
| Lambda behavior | **Passed with mocks** | Three report writes, encryption argument, fixed configured destination, alert behavior, partial-scan errors and storage failures |
| Deployable ZIP build | **Passed** | `scripts/build_lambda.py` bundled the application and pinned SDK dependencies; ZIP integrity checked |
| Isolated ZIP import | **Passed** | Extracted bundle imported Boto3 and the Lambda handler and evaluated the demo using Python `-S`, without system site-packages |
| Terraform HCL syntax | **Passed** | All four `.tf` files parsed with `python-hcl2` |
| Workflow YAML syntax | **Passed** | Both GitHub workflow files parsed successfully |
| Terraform formatting/provider validation | **Passed in CI** | The supplied CI step completed Terraform formatting, backend-free initialization and validation; no account-specific plan or apply was executed |
| Docker build/run | **Passed in CI** | Image build and container-output smoke test completed successfully |
| Browser rendering/filter interaction | **Passed in CI** | Chromium checked priority and region filters, search with no matches, restored finding count, mobile overflow, expanded recommendations and JavaScript page errors |
| Screenshot visual review | **Passed** | Reviewed both full-page PNGs: desktop at 1365 px wide and mobile at 390 px wide; synthetic-data labels, totals, cards and recommendations are visible without clipping |
| GitHub Actions execution | **Passed** | The linked `test-and-package` job completed successfully, including artifact upload |
| Live AWS scan, IAM, Terraform apply, SNS delivery and DLQs | **Not run** | No AWS account was connected or provisioned |

## Test coverage

The 22 tests cover:

- Expected demo counts and a genuinely empty inventory.
- Attached/creating volumes, address associations and required/blank tags.
- Numeric TCP protocols, port ranges, IPv6, all-protocol rules and safe-rule exclusions.
- Terminated instances and stable account-scoped finding IDs.
- Partial inventory, later-page errors and continued collection.
- HTML escaping, placeholder injection and CSV formula protection.
- Parseable report exports and CLI exit-code semantics.
- Lambda report storage, alerts and failure propagation.

Run the browser check after installing its optional dependencies:

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/check_report_browser.py
```

The desktop and mobile screenshots have been visually reviewed, and the automated browser checks passed in Chromium. This is evidence for the synthetic report UI and build pipeline. Complete the deployment checks before describing the project as deployed to AWS.
