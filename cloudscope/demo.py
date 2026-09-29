"""Synthetic data only: documentation IP ranges and invented resource IDs."""

from copy import deepcopy


def tags(name, owner="platform", environment="dev", project="cloudscope"):
    return [{"Key": key, "Value": value} for key, value in
            {"Name": name, "Owner": owner, "Environment": environment, "Project": project}.items()]


DATA = {
    "mode": "demo", "account_id": "000000000000", "collected_at": "2026-09-29T10:30:00+00:00", "errors": [],
    "regions": {
        "ap-south-1": {
            "instances": [
                {"InstanceId": "i-demo-web", "State": {"Name": "running"}, "Tags": tags("web-service")},
                {"InstanceId": "i-demo-worker", "State": {"Name": "stopped"}, "Tags": tags("batch-worker", owner="")},
            ],
            "volumes": [
                {"VolumeId": "vol-demo-orphan", "State": "available", "Attachments": [], "Size": 80,
                 "VolumeType": "gp3", "Encrypted": True, "Tags": tags("old-build-cache")},
                {"VolumeId": "vol-demo-legacy", "State": "in-use", "Attachments": [{"InstanceId": "i-demo-web"}],
                 "Size": 30, "VolumeType": "gp3", "Encrypted": False, "Tags": tags("legacy-data", project="")},
                {"VolumeId": "vol-demo-root", "State": "in-use", "Attachments": [{"InstanceId": "i-demo-web"}],
                 "Size": 20, "VolumeType": "gp3", "Encrypted": True, "Tags": tags("web-root")},
            ],
            "addresses": [
                {"AllocationId": "eipalloc-demo-spare", "PublicIp": "192.0.2.10", "Tags": tags("spare-address")},
                {"AllocationId": "eipalloc-demo-web", "PublicIp": "192.0.2.11", "AssociationId": "eipassoc-demo", "NetworkInterfaceId": "eni-demo"},
            ],
            "security_groups": [
                {"GroupId": "sg-demo-admin", "Tags": tags("legacy-admin"), "IpPermissions": [
                    {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                    {"IpProtocol": "tcp", "FromPort": 3389, "ToPort": 3389, "Ipv6Ranges": [{"CidrIpv6": "::/0"}]},
                ]},
                {"GroupId": "sg-demo-web", "Tags": tags("public-web"), "IpPermissions": [
                    {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                ]},
            ],
        },
        "ap-southeast-1": {
            "instances": [{"InstanceId": "i-demo-api", "State": {"Name": "running"}, "Tags": tags("api-service")}],
            "volumes": [{"VolumeId": "vol-demo-backup", "State": "available", "Attachments": [], "Size": 40,
                         "VolumeType": "gp3", "Encrypted": True, "Tags": tags("retired-backup")}],
            "addresses": [], "security_groups": [],
        },
    },
}


def inventory():
    return deepcopy(DATA)
