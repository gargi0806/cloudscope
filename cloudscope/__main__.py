"""python -m cloudscope demo | scan"""

import argparse
import sys

from .audit import DEFAULT_TAGS, audit
from .demo import inventory
from .report import write_reports


def main(argv=None):
    parser = argparse.ArgumentParser(description="CloudScope — read-only AWS resource audit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("demo", "scan"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--out", default="reports", help="Report directory (overwrites report.* files)")
        sub.add_argument("--required-tags", nargs="+", default=list(DEFAULT_TAGS))
        sub.add_argument("--fail-on", choices=("high", "medium", "low"), help="Exit 1 for findings at this severity or higher")
        if command == "scan":
            sub.add_argument("--regions", nargs="+", default=["ap-south-1"])
            sub.add_argument("--profile", help="AWS CLI profile; defaults to the standard credential chain")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            data = inventory()
        else:
            import boto3
            from .collector import collect
            data = collect(boto3.Session(profile_name=args.profile), args.regions)
        report = audit(data, args.required_tags)
        folder = write_reports(report, args.out)
    except Exception as exc:
        print(f"Scan failed ({type(exc).__name__}). Check dependencies, AWS login/profile, permissions and output directory. No successful scan was produced.", file=sys.stderr)
        return 2
    print(f"CloudScope | {report['mode'].upper()} | {report['status'].upper()}")
    print(f"{report['resources_scanned']} resources | {len(report['findings'])} findings | {report['summary']}")
    print(f"Reports: {folder}")
    if report["errors"]:
        print(f"WARNING: {len(report['errors'])} collection errors; inspect report.json.", file=sys.stderr)
        return 2
    if args.fail_on:
        levels = ("high", "medium", "low")
        return int(any(report["summary"][level] for level in levels[:levels.index(args.fail_on) + 1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
