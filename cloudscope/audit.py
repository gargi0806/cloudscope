"""Pure, deterministic audit rules. No network calls or resource mutations."""

import hashlib
from datetime import datetime, timezone

DEFAULT_TAGS = ("Owner", "Environment", "Project")
SEVERITIES = {"high": 0, "medium": 1, "low": 2}


def tag_map(resource):
    return {t["Key"]: t.get("Value", "") for t in resource.get("Tags", [])}


def audit(inventory, required_tags=DEFAULT_TAGS):
    """Evaluate normalized EC2 inventory; preserve collection errors in the report."""
    findings = []
    counts = {key: 0 for key in ("instances", "volumes", "addresses", "security_groups")}
    account = inventory.get("account_id", "unknown")

    def add(region, resource, rid, rule, severity, title, evidence, recommendation):
        identity = f"{account}:{region}:{rid}:{rule}"
        findings.append({
            "id": hashlib.sha256(identity.encode()).hexdigest()[:16],
            "rule": rule, "severity": severity, "title": title,
            "resource_id": rid, "name": tag_map(resource).get("Name", rid),
            "region": region, "evidence": evidence, "recommendation": recommendation,
        })

    for region, data in sorted(inventory.get("regions", {}).items()):
        for key in counts:
            counts[key] += len(data.get(key, []))
        for volume in data.get("volumes", []):
            rid = volume["VolumeId"]
            if volume.get("State") == "available" and not volume.get("Attachments"):
                add(region, volume, rid, "EBS_UNATTACHED", "medium", "Unattached EBS volume",
                    f"{volume.get('Size', '?')} GiB {volume.get('VolumeType', 'unknown')} volume is available with no attachments.",
                    "Confirm the owner and retention needs. Snapshot if required, then approve deletion manually. Creation time is not detachment time.")
            if volume.get("Encrypted") is False:
                add(region, volume, rid, "EBS_UNENCRYPTED", "medium", "EBS encryption disabled",
                    "The volume reports Encrypted=false.",
                    "Plan a tested migration using an encrypted snapshot copy and replacement volume. Existing volumes cannot be encrypted in place.")
        for address in data.get("addresses", []):
            if not address.get("AssociationId") and not address.get("NetworkInterfaceId"):
                rid = address.get("AllocationId", address.get("PublicIp", "unknown-address"))
                add(region, address, rid, "EIP_UNASSOCIATED", "medium", "Unassociated Elastic IP",
                    f"{address.get('PublicIp', 'Unknown IP')} has no association or network interface.",
                    "Check DNS, allowlists and disaster-recovery requirements before releasing it. Review actual billing; this is not a savings estimate.")
        for kind, id_key in (("instances", "InstanceId"), ("volumes", "VolumeId")):
            for resource in data.get(kind, []):
                if kind == "instances" and resource.get("State", {}).get("Name") in ("terminated", "shutting-down"):
                    continue
                tags = tag_map(resource)
                missing = [key for key in required_tags if not str(tags.get(key, "")).strip()]
                if missing:
                    add(region, resource, resource[id_key], "REQUIRED_TAGS", "low", "Missing ownership tags",
                        "Missing or empty tags: " + ", ".join(missing),
                        "Confirm the resource owner, then add the required tags through your infrastructure configuration.")
        for group in data.get("security_groups", []):
            exposures = set()
            for permission in group.get("IpPermissions", []):
                protocol = str(permission.get("IpProtocol", ""))
                if protocol not in ("tcp", "6", "-1"):
                    continue
                sources = [r.get("CidrIp") for r in permission.get("IpRanges", [])]
                sources += [r.get("CidrIpv6") for r in permission.get("Ipv6Ranges", [])]
                public = sorted(set(sources) & {"0.0.0.0/0", "::/0"})
                if not public:
                    continue
                ports = (22, 3389) if protocol == "-1" else tuple(
                    port for port in (22, 3389)
                    if permission.get("FromPort", 65536) <= port <= permission.get("ToPort", -1)
                )
                for port in ports:
                    for source in public:
                        exposures.add(f"TCP {port} from {source}")
            if exposures:
                add(region, group, group["GroupId"], "SG_PUBLIC_ADMIN", "high", "Public administration rule",
                    "; ".join(sorted(exposures)) + ". Rule configuration only; attachment and network reachability are not assessed.",
                    "Review dependencies. Prefer Systems Manager Session Manager, or restrict administration to approved source networks.")
    findings.sort(key=lambda f: (SEVERITIES[f["severity"]], f["region"], f["resource_id"], f["rule"]))
    errors = inventory.get("errors", [])
    return {
        "schema_version": "1.0", "project": "CloudScope",
        "mode": inventory.get("mode", "live"), "account_id": account,
        "generated_at": inventory.get("collected_at", datetime.now(timezone.utc).isoformat()),
        "status": "partial" if errors else "complete",
        "regions": sorted(inventory.get("regions", {})), "required_tags": list(required_tags),
        "resource_counts": counts, "resources_scanned": sum(counts.values()),
        "summary": {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES},
        "findings": findings, "errors": errors,
    }
