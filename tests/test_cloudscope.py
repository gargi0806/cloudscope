import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import boto3
from botocore.stub import Stubber

from cloudscope.__main__ import main
from cloudscope.audit import audit
from cloudscope.collector import collect
from cloudscope.demo import inventory, tags
from cloudscope.handler import handler
from cloudscope.report import csv_report, html_report, write_reports


def empty_inventory():
    return {"mode": "live", "account_id": "123456789012", "errors": [], "regions": {"ap-south-1": {
        "instances": [], "volumes": [], "addresses": [], "security_groups": []}}}


class RuleTests(unittest.TestCase):
    def test_demo_expected_findings_and_resource_count(self):
        report = audit(inventory())
        self.assertEqual(report["summary"], {"high": 1, "medium": 4, "low": 2})
        self.assertEqual(report["resources_scanned"], 11)
        self.assertEqual(report["status"], "complete")

    def test_empty_account_is_complete_with_no_findings(self):
        report = audit(empty_inventory())
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["resources_scanned"], 0)

    def test_attached_and_creating_volumes_are_not_flagged_unattached(self):
        data = inventory()
        data["regions"]["ap-south-1"]["volumes"][0]["State"] = "creating"
        data["regions"]["ap-southeast-1"]["volumes"][0]["Attachments"] = [{"InstanceId": "i-held"}]
        self.assertNotIn("EBS_UNATTACHED", [f["rule"] for f in audit(data)["findings"]])

    def test_network_interface_association_prevents_unused_ip_finding(self):
        data = inventory()
        data["regions"]["ap-south-1"]["addresses"][0]["NetworkInterfaceId"] = "eni-service"
        self.assertNotIn("EIP_UNASSOCIATED", [f["rule"] for f in audit(data)["findings"]])

    def test_all_protocols_with_ipv6_is_flagged_once(self):
        data = empty_inventory()
        data["regions"]["ap-south-1"]["security_groups"] = [{"GroupId": "sg-open", "IpPermissions": [
            {"IpProtocol": "-1", "Ipv6Ranges": [{"CidrIpv6": "::/0"}]}]}]
        findings = audit(data)["findings"]
        self.assertEqual(len(findings), 1)
        self.assertIn("TCP 22", findings[0]["evidence"])
        self.assertIn("TCP 3389", findings[0]["evidence"])

    def test_private_admin_udp_and_https_are_not_flagged(self):
        data = empty_inventory()
        data["regions"]["ap-south-1"]["security_groups"] = [{"GroupId": "sg-safe", "IpPermissions": [
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "10.0.0.0/8"}]},
            {"IpProtocol": "udp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        ]}]
        self.assertEqual(audit(data)["findings"], [])

    def test_numeric_tcp_and_port_ranges_are_supported(self):
        data = empty_inventory()
        data["regions"]["ap-south-1"]["security_groups"] = [{"GroupId": "sg-range", "IpPermissions": [
            {"IpProtocol": "6", "FromPort": 0, "ToPort": 100, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]}]
        evidence = audit(data)["findings"][0]["evidence"]
        self.assertIn("TCP 22", evidence)
        self.assertNotIn("3389", evidence)

    def test_terminated_instances_do_not_get_tag_findings(self):
        data = empty_inventory()
        data["regions"]["ap-south-1"]["instances"] = [{"InstanceId": "i-gone", "State": {"Name": "terminated"}}]
        self.assertEqual(audit(data)["findings"], [])

    def test_blank_and_custom_tags_are_checked(self):
        data = empty_inventory()
        data["regions"]["ap-south-1"]["instances"] = [{"InstanceId": "i-test", "Tags": [{"Key": "Team", "Value": "  "}]}]
        report = audit(data, ("Team",))
        self.assertEqual(len(report["findings"]), 1)
        self.assertEqual(report["findings"][0]["evidence"], "Missing or empty tags: Team")

    def test_ids_are_stable_but_account_scoped(self):
        data = inventory()
        first = audit(data)["findings"][0]["id"]
        self.assertEqual(first, audit(data)["findings"][0]["id"])
        data["account_id"] = "111111111111"
        self.assertNotEqual(first, audit(data)["findings"][0]["id"])

    def test_errors_never_appear_as_complete_scan(self):
        data = empty_inventory()
        data["errors"] = [{"region": "ap-south-1", "operation": "describe_volumes", "code": "UnauthorizedOperation"}]
        self.assertEqual(audit(data)["status"], "partial")
        self.assertIn("Incomplete scan", html_report(audit(data)))


class ReportTests(unittest.TestCase):
    def test_html_escapes_tags_and_does_not_expand_injected_placeholders(self):
        data = inventory()
        data["regions"]["ap-south-1"]["volumes"][0]["Tags"] = tags('<script>alert(1)</script>@@LABEL@@')
        output = html_report(audit(data))
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;@@LABEL@@", output)

    def test_csv_neutralizes_spreadsheet_formulas(self):
        report = audit(inventory())
        report["findings"][0]["name"] = "  =HYPERLINK(\"https://example.com\")"
        rows = list(csv.DictReader(io.StringIO(csv_report(report))))
        self.assertTrue(rows[0]["name"].startswith("'"))

    def test_report_files_are_parseable_and_self_contained(self):
        report = audit(inventory())
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, directory)
            folder = Path(directory)
            self.assertEqual(json.loads((folder / "report.json").read_text())["summary"], report["summary"])
            self.assertEqual(len(list(csv.DictReader(io.StringIO((folder / "report.csv").read_text())))), 7)
            self.assertNotIn('<script src=', (folder / "report.html").read_text())

    def test_cli_demo_failure_threshold_and_default_exit(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--out", directory]), 0)
            self.assertEqual(main(["demo", "--out", directory, "--fail-on", "high"]), 1)

    def test_cli_partial_scan_exit_two(self):
        data = empty_inventory()
        data["errors"] = [{"region": "ap-south-1", "operation": "describe_volumes", "code": "Denied"}]
        with tempfile.TemporaryDirectory() as directory, patch("cloudscope.collector.collect", return_value=data), patch("boto3.Session"), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["scan", "--out", directory]), 2)
            self.assertEqual(json.loads((Path(directory) / "report.json").read_text())["status"], "partial")


class CollectionTests(unittest.TestCase):
    def setUp(self):
        session = boto3.Session(aws_access_key_id="testing", aws_secret_access_key="testing", region_name="ap-south-1")
        self.sts = session.client("sts")
        self.ec2 = session.client("ec2")
        self.sts_stub, self.ec2_stub = Stubber(self.sts), Stubber(self.ec2)
        self.sts_stub.add_response("get_caller_identity", {"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/test", "UserId": "test"}, {})
        self.session = SimpleNamespace(client=lambda service, **kwargs: {"sts": self.sts, "ec2": self.ec2}[service])

    def tail(self):
        self.ec2_stub.add_response("describe_addresses", {"Addresses": []}, {})
        self.ec2_stub.add_response("describe_instances", {"Reservations": [{"Instances": [{"InstanceId": "i-example", "State": {"Name": "running"}}]}]}, {})
        self.ec2_stub.add_response("describe_security_groups", {"SecurityGroups": []}, {})

    def test_real_sdk_pagination_and_reservation_flattening(self):
        self.ec2_stub.add_response("describe_volumes", {"Volumes": [{"VolumeId": "vol-page-one"}], "NextToken": "page2"}, {})
        self.ec2_stub.add_response("describe_volumes", {"Volumes": [{"VolumeId": "vol-page-two"}]}, {"NextToken": "page2"})
        self.tail()
        with self.sts_stub, self.ec2_stub:
            data = collect(self.session, ["ap-south-1", "ap-south-1"])
            self.assertEqual(len(data["regions"]["ap-south-1"]["volumes"]), 2)
            self.assertEqual(data["regions"]["ap-south-1"]["instances"][0]["InstanceId"], "i-example")
            self.assertEqual(data["errors"], [])
            self.ec2_stub.assert_no_pending_responses()

    def test_failure_on_later_page_preserves_data_and_continues(self):
        self.ec2_stub.add_response("describe_volumes", {"Volumes": [{"VolumeId": "vol-first"}], "NextToken": "page2"}, {})
        self.ec2_stub.add_client_error("describe_volumes", service_error_code="UnauthorizedOperation", expected_params={"NextToken": "page2"})
        self.tail()
        with self.sts_stub, self.ec2_stub:
            data = collect(self.session, ["ap-south-1"])
            self.assertEqual(len(data["regions"]["ap-south-1"]["volumes"]), 1)
            self.assertEqual(data["errors"][0]["code"], "UnauthorizedOperation")
            self.assertEqual(len(data["regions"]["ap-south-1"]["instances"]), 1)
            self.ec2_stub.assert_no_pending_responses()


class LambdaTests(unittest.TestCase):
    def invoke(self, data, s3=None, sns=None):
        s3, sns = s3 or MagicMock(), sns or MagicMock()
        environment = {"SCAN_REGIONS": "ap-south-1", "REPORT_BUCKET": "test-reports", "ALERT_TOPIC_ARN": "arn:aws:sns:ap-south-1:123456789012:test"}
        with patch.dict(os.environ, environment), patch("cloudscope.handler.collect", return_value=data), patch("boto3.Session"), patch("boto3.client", side_effect=lambda service: {"s3": s3, "sns": sns}[service]), redirect_stdout(io.StringIO()):
            result = handler({"REPORT_BUCKET": "attacker-bucket"}, SimpleNamespace(aws_request_id="run-123"))
        return result, s3, sns

    def test_reports_are_private_destination_encrypted_and_alerted(self):
        result, s3, sns = self.invoke(inventory())
        self.assertEqual(s3.put_object.call_count, 3)
        for call in s3.put_object.call_args_list:
            self.assertEqual(call.kwargs["Bucket"], "test-reports")
            self.assertEqual(call.kwargs["ServerSideEncryption"], "AES256")
            self.assertNotIn("ACL", call.kwargs)
        self.assertEqual(result["status"], "complete")
        sns.publish.assert_called_once()

    def test_empty_success_does_not_send_finding_alert(self):
        result, _, sns = self.invoke(empty_inventory())
        self.assertEqual(result["findings"]["high"], 0)
        sns.publish.assert_not_called()

    def test_partial_scan_saves_reports_then_raises(self):
        data, s3, sns = empty_inventory(), MagicMock(), MagicMock()
        data["errors"] = [{"region": "ap-south-1", "operation": "describe_volumes", "code": "Denied"}]
        with self.assertRaisesRegex(RuntimeError, "Partial scan"):
            self.invoke(data, s3, sns)
        self.assertEqual(s3.put_object.call_count, 3)
        sns.publish.assert_called_once()

    def test_storage_failure_is_not_reported_as_success(self):
        s3, sns = MagicMock(), MagicMock()
        s3.put_object.side_effect = RuntimeError("S3 unavailable")
        with self.assertRaisesRegex(RuntimeError, "S3 unavailable"):
            self.invoke(inventory(), s3, sns)
        sns.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
