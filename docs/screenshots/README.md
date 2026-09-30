# Demo screenshots

These are unmodified Chromium screenshots of CloudScope's synthetic HTML report. The report uses fictional resources and account `000000000000`; no AWS account was accessed. They demonstrate the application UI, not an AWS deployment.

| File | Full image size | Capture state |
|---|---|---|
| [desktop.png](desktop.png) | 1365 × 2032 px | All seven findings; all priorities and regions; empty search; recommendations collapsed |
| [mobile.png](mobile.png) | 390 × 3242 px | Same findings with the first recommendation expanded |

## Provenance

- Captured on 29 September 2026 by [`scripts/check_report_browser.py`](../../scripts/check_report_browser.py), using Playwright and Chromium.
- Source commit: [`10f38f5c2aaef7ded7675f1eeaa33b2771b01bf9`](https://github.com/gargi0806/cloudscope/commit/10f38f5c2aaef7ded7675f1eeaa33b2771b01bf9).
- Successful workflow: [CloudScope CI, run 36578857204](https://github.com/gargi0806/cloudscope/actions/runs/36578857204).
- Artifact: `cloudscope-build`, ID `11039105765`; original paths `reports/screenshots/desktop.png` and `reports/screenshots/mobile.png`.
- The script starts with a 1365 × 1000 desktop viewport, then switches to 390 × 844 for mobile. Both images capture the entire page.

## Recreate

From the repository root:

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/check_report_browser.py
```

New images are written to `reports/screenshots/`. Font rendering and browser versions can change image pixels between runs.
