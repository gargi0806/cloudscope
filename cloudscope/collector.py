"""AWS inventory collection with pagination and explicit partial-failure handling."""

from datetime import datetime, timezone


def collect(session, regions):
    # Lazy dependency import keeps the offline demo usable with only Python.
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError

    config = Config(retries={"mode": "standard", "total_max_attempts": 3},
                    connect_timeout=5, read_timeout=20)
    account = session.client("sts", region_name=regions[0], config=config).get_caller_identity()["Account"]
    inventory = {"mode": "live", "account_id": account,
                 "collected_at": datetime.now(timezone.utc).isoformat(), "regions": {}, "errors": []}
    operations = (("volumes", "describe_volumes", "Volumes"),
                  ("addresses", "describe_addresses", "Addresses"),
                  ("instances", "describe_instances", "Reservations"),
                  ("security_groups", "describe_security_groups", "SecurityGroups"))
    for region in dict.fromkeys(regions):
        data = inventory["regions"][region] = {key: [] for key, _, _ in operations}
        try:
            client = session.client("ec2", region_name=region, config=config)
        except (BotoCoreError, ClientError) as exc:
            inventory["errors"].append({"region": region, "operation": "create_client", "code": type(exc).__name__})
            continue
        for key, operation, response_key in operations:
            try:
                if client.can_paginate(operation):
                    pages = client.get_paginator(operation).paginate()
                else:
                    pages = [getattr(client, operation)()]
                for page in pages:
                    items = page.get(response_key, [])
                    if key == "instances":
                        items = [instance for reservation in items for instance in reservation.get("Instances", [])]
                    data[key].extend(items)
            except (BotoCoreError, ClientError) as exc:
                # Keep previous successful pages, but never label incomplete inventory healthy.
                code = exc.response["Error"]["Code"] if isinstance(exc, ClientError) else type(exc).__name__
                inventory["errors"].append({"region": region, "operation": operation, "code": code})
    return inventory
