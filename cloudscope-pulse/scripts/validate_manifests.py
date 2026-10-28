"""Static checks runnable without Docker, kubectl or access to AWS."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
paths = list((ROOT / 'k8s').rglob('*.yaml'))
assert paths, 'no manifests found'
for path in paths:
    with path.open() as stream:
        documents = [doc for doc in yaml.safe_load_all(stream) if doc]
    assert documents, f'empty YAML: {path}'
    for doc in documents:
        assert isinstance(doc, dict) and 'kind' in doc and 'apiVersion' in doc, path
        if doc['kind'] == 'Deployment':
            container = doc['spec']['template']['spec']['containers'][0]
            assert container['securityContext']['allowPrivilegeEscalation'] is False
            assert container['securityContext']['readOnlyRootFilesystem'] is True
            assert container['resources']['requests']['cpu']
            assert container['readinessProbe']
print(f'Checked {len(paths)} Kubernetes YAML files for syntax and baseline deployment safeguards')
