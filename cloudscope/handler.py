"""Scheduled Lambda entry point. Writes reports, never mutates scanned resources."""

import json
import os
import re

from .audit import DEFAULT_TAGS, audit
from .collector import collect
from .report import payloads


def handler(event, context):
    import boto3

    regions = [value.strip() for value in os.environ["SCAN_REGIONS"].split(",") if value.strip()]
    required_tags = [value.strip() for value in os.environ.get("REQUIRED_TAGS", ",".join(DEFAULT_TAGS)).split(",") if value.strip()]
    if not regions:
        raise ValueError("SCAN_REGIONS must contain at least one region")
    report = audit(collect(boto3.Session(), regions), required_tags)
    # Do not allow event input to choose the destination, region set or AWS role.
    run_id = re.sub(r"[^A-Za-z0-9_-]", "_", context.aws_request_id)
    key_prefix = f"reports/{report['generated_at'][:10]}/{run_id}"
    bucket = os.environ["REPORT_BUCKET"]
    s3 = boto3.client("s3")
    for filename, (body, content_type) in payloads(report).items():
        s3.put_object(Bucket=bucket, Key=f"{key_prefix}/{filename}", Body=body.encode("utf-8"),
                      ContentType=content_type, ServerSideEncryption="AES256")
    summary = {"status": report["status"], "resources_scanned": report["resources_scanned"],
               "findings": report["summary"], "collection_errors": len(report["errors"]),
               "report_uri": f"s3://{bucket}/{key_prefix}/report.html"}
    print(json.dumps({"event": "scan_complete", **summary}))
    topic = os.environ.get("ALERT_TOPIC_ARN")
    if topic and (report["summary"]["high"] or report["errors"]):
        boto3.client("sns").publish(TopicArn=topic, Subject="CloudScope: audit requires review",
                                    Message=json.dumps(summary, indent=2))
    if report["errors"]:
        # A saved partial report is not a successful scheduled scan.
        raise RuntimeError(f"Partial scan: {len(report['errors'])} collection errors. Report saved to {summary['report_uri']}")
    return summary
