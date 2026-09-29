"""Portable JSON, CSV and self-contained interactive HTML reports."""

import csv
import html
import io
import json
from pathlib import Path


def csv_report(report):
    output = io.StringIO(newline="")
    columns = ("id", "severity", "rule", "resource_id", "name", "region", "title", "evidence", "recommendation")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for finding in report["findings"]:
        # Prevent spreadsheet formula execution in externally controlled resource tags.
        row = {key: str(finding[key]) for key in columns}
        writer.writerow({key: "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
                         for key, value in row.items()})
    return output.getvalue()


def html_report(report):
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for finding in report["findings"]:
        severity = finding["severity"]
        cards.append(f'''<article class="finding" data-severity="{esc(severity)}" data-region="{esc(finding['region'])}">
<div class="finding-top"><span class="pill {esc(severity)}">{esc(severity)}</span><span class="rule">{esc(finding['rule'])}</span></div>
<h3>{esc(finding['title'])}</h3><p class="resource">{esc(finding['name'])} <span>· {esc(finding['resource_id'])}</span></p>
<p>{esc(finding['evidence'])}</p><details><summary>Recommended review</summary><p>{esc(finding['recommendation'])}</p></details>
<div class="finding-bottom">{esc(finding['region'])}<span>#{esc(finding['id'][:8])}</span></div></article>''')
    options = ''.join(f'<option value="{esc(region)}">{esc(region)}</option>' for region in report['regions'])
    errors = ''.join(f"<li>{esc(e['region'])} / {esc(e['operation'])}: {esc(e['code'])}</li>" for e in report['errors'])
    warning = f'<section class="warning"><strong>Incomplete scan — findings may be missing.</strong><ul>{errors}</ul></section>' if errors else ''
    demo = report['mode'] == 'demo'
    label = 'SYNTHETIC DEMO' if demo else 'LIVE AWS SCAN'
    note = 'Sample resources only. No AWS account was accessed.' if demo else 'Read-only scan. Findings require human review; no resources were changed.'
    stats = ''.join(f'<div class="stat"><span>{label}</span><strong>{value}</strong></div>' for label, value in (
        ('Resources scanned', report['resources_scanned']), ('High priority', report['summary']['high']),
        ('Review recommended', report['summary']['medium']), ('Tagging gaps', report['summary']['low'])))
    template = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CloudScope | AWS resource audit</title><style>
:root{color-scheme:dark;--bg:#0c1220;--panel:#141e30;--line:#2a374c;--text:#ecf3ff;--muted:#a8b9cf;--teal:#72e8ca}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}
.shell{max-width:1200px;margin:auto;padding:34px 32px 50px}header{display:flex;justify-content:space-between;align-items:center;gap:16px;border-bottom:1px solid var(--line);padding-bottom:23px}
.brand{font-size:23px;letter-spacing:-1px;font-weight:750}.brand b{color:var(--teal)}.eyebrow{font-size:11px;font-weight:700;letter-spacing:2px;color:var(--teal)}.status{border:1px solid #40635e;background:#102e2c;border-radius:30px;padding:5px 12px;font-size:11px;color:var(--teal);white-space:nowrap}
.hero{padding:44px 0 26px;max-width:850px}h1{font-size:clamp(30px,5vw,49px);letter-spacing:-2px;line-height:1.13;margin:14px 0 18px}h1 span{color:var(--teal)}.hero p{color:var(--muted);max-width:650px;margin:0}.meta{font-size:12px;color:var(--muted);margin-top:16px;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:14px;background:var(--panel);margin:8px 0 34px}.stat{padding:22px 25px;border-right:1px solid var(--line)}.stat:last-child{border:0}.stat span{color:var(--muted);font-size:12px;display:block}.stat strong{font-size:34px;line-height:1.5}
.section-top{display:flex;align-items:center;justify-content:space-between;gap:12px}h2{font-size:21px;letter-spacing:-.5px}#count{color:var(--muted);font-size:12px}.filters{display:grid;grid-template-columns:2fr 1fr 1fr;gap:14px;margin:8px 0 24px}label{font-size:12px;color:var(--muted)}input,select{display:block;width:100%;margin-top:5px;border:1px solid var(--line);background:var(--panel);border-radius:8px;color:var(--text);padding:12px;font:inherit;font-size:13px}input:focus,select:focus,summary:focus{outline:2px solid var(--teal);outline-offset:3px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.finding{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px;overflow-wrap:anywhere}.finding[hidden]{display:none}.finding-top,.finding-bottom{display:flex;align-items:center;justify-content:space-between;gap:8px}.pill{border-radius:5px;padding:3px 8px;text-transform:uppercase;font-size:10px;font-weight:750;letter-spacing:1px}.high{background:#502b39;color:#ffadbb}.medium{background:#453924;color:#f9d38b}.low{background:#243c55;color:#a6d3ff}.rule{color:var(--muted);font:10px ui-monospace,monospace}.finding h3{font-size:19px;letter-spacing:-.3px;margin:16px 0 4px}.finding p{font-size:13px;color:#bfcee0;margin:10px 0 16px}.finding p.resource{color:var(--teal);font-size:12px}.resource span{color:var(--muted)}details{border-top:1px solid var(--line);padding-top:12px}summary{cursor:pointer;font-size:12px;font-weight:600;color:var(--text)}.finding-bottom{margin-top:20px;font:11px ui-monospace,monospace;color:var(--muted)}.finding-bottom span{opacity:.65}.warning{background:#47341f;border:1px solid #a67c40;border-radius:10px;padding:18px;margin-bottom:24px}.empty{padding:30px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:12px}footer{margin-top:32px;border-top:1px solid var(--line);padding-top:18px;font-size:11px;color:var(--muted)}noscript{color:#f9d38b}
@media(max-width:650px){.shell{padding:22px 18px}.hero{padding-top:30px}h1{letter-spacing:-1px}.stats{grid-template-columns:1fr 1fr}.stat{padding:17px}.stat:nth-child(2){border-right:0}.stat:nth-child(-n+2){border-bottom:1px solid var(--line)}.grid,.filters{grid-template-columns:1fr}.rule{font-size:9px}.finding{padding:18px}header{align-items:flex-start}.brand{font-size:22px}}
@media print{body{background:white;color:#111}.filters,header .status{display:none}.finding,.stats{background:white;color:#111;break-inside:avoid}.finding p,.meta,footer,.stat span,.rule{color:#333}.grid{display:block}.finding{margin-bottom:12px}details{display:block}}
</style></head><body><main class="shell"><header><div class="brand">cloud<b>scope</b><div class="eyebrow">AWS RESOURCE INTELLIGENCE</div></div><span class="status">@@LABEL@@</span></header>
<section class="hero"><div class="eyebrow">VISIBILITY BEFORE ACTION</div><h1>A clearer view of<br>your <span>cloud footprint.</span></h1><p>Find overlooked resources, ownership gaps and risky administration rules. Prioritize the next review with evidence from your AWS inventory.</p><div class="meta">@@NOTE@@<br>Account @@ACCOUNT@@ · @@TIME@@ · Scan status: @@STATUS@@</div></section>
@@WARNING@@<section class="stats" aria-label="Scan summary">@@STATS@@</section>
<section aria-label="Audit findings"><div class="section-top"><h2>Findings to review</h2><span id="count" aria-live="polite">@@TOTAL@@ findings</span></div><noscript>All findings are shown. Enable JavaScript to use search and filters.</noscript>
<div class="filters"><label>Search resources or rules<input id="search" type="search" placeholder="Try volume, SSH or a resource ID"></label><label>Priority<select id="severity"><option value="all">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></label><label>Region<select id="region"><option value="all">All regions</option>@@OPTIONS@@</select></label></div>
<div class="grid">@@CARDS@@</div><p class="empty" id="empty" @@HIDDEN@@>@@EMPTY@@</p></section><footer>CloudScope 1.0 · Five focused audit rules · A point-in-time review, not a complete security assessment or billing forecast.<br>Reports can contain account identifiers and resource tags. Share only synthetic demo reports publicly.</footer></main>
<script>const cards=[...document.querySelectorAll('.finding')],search=document.getElementById('search'),severity=document.getElementById('severity'),region=document.getElementById('region');function filter(){let visible=0;for(const card of cards){const show=card.textContent.toLowerCase().includes(search.value.toLowerCase().trim())&&(severity.value==='all'||card.dataset.severity===severity.value)&&(region.value==='all'||card.dataset.region===region.value);card.hidden=!show;if(show)visible++;}document.getElementById('count').textContent=visible+' of '+cards.length+' findings';document.getElementById('empty').hidden=visible!==0;}[search,severity,region].forEach(el=>el.addEventListener('input',filter));</script></body></html>'''
    values = {"LABEL": esc(label), "NOTE": esc(note), "ACCOUNT": esc(report["account_id"]),
              "TIME": esc(report["generated_at"]), "STATUS": esc(report["status"]), "WARNING": warning,
              "STATS": stats, "TOTAL": str(len(cards)), "OPTIONS": options, "CARDS": ''.join(cards),
              "HIDDEN": 'hidden' if cards else '', "EMPTY": "No matching findings." if cards else
              ("No findings in the available inventory. Scan incomplete; review collection errors." if report["errors"] else "No findings for the five configured rules.")}
    # Substitute once so resource names cannot inject further template placeholders.
    import re
    return re.sub(r"@@([A-Z]+)@@", lambda match: values[match.group(1)], template)


def payloads(report):
    return {"report.json": (json.dumps(report, indent=2) + "\n", "application/json"),
            "report.csv": (csv_report(report), "text/csv; charset=utf-8"),
            "report.html": (html_report(report), "text/html; charset=utf-8")}


def write_reports(report, output):
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    for filename, (body, _) in payloads(report).items():
        (folder / filename).write_text(body, encoding="utf-8")
    return folder.resolve()
