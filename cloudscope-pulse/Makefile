.PHONY: test run docker-build kind deploy fmt validate

test:
	python -m pytest -q tests

run:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

docker-build:
	docker build -t cloudscope-pulse:dev .

kind:
	./scripts/local-kind.sh

fmt:
	terraform -chdir=terraform fmt -recursive

validate:
	python scripts/validate_manifests.py
	terraform -chdir=terraform init -backend=false
	terraform -chdir=terraform validate
