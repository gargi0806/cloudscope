# Validation record

Build prepared on 29 September 2026. These results describe this delivered source package, not an AWS production deployment.

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
| Terraform provider validation/plan | **Not run** | Terraform was unavailable and the binary download timed out; run the supplied CI or local `init`/`validate`/`plan` |
| Docker build/run | **Not run** | No Docker executable in the delivery environment; CI includes a build and container-output check |
| Browser rendering/filter interaction | **Not run** | Playwright was available but no browser binary was installed; browser download failed. `scripts/check_report_browser.py` and CI provide desktop/mobile, filter and overflow checks |
| GitHub Actions execution | **Not run** | Workflows have been supplied, not pushed or executed in a connected repository |
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

The UI is written with responsive CSS, but this delivery does not claim a completed visual review. The source, synthetic demo and local scanner are usable immediately; complete the deployment checks before describing it as a deployed AWS project.
