#!/usr/bin/env bash
set -euo pipefail
for bin in aws docker git terraform; do command -v "$bin" >/dev/null || { echo "Missing prerequisite: $bin" >&2; exit 1; }; done
: "${AWS_REGION:?Export AWS_REGION e.g. ap-south-1}"
IMAGE_REPOSITORY=$(terraform -chdir=terraform output -raw ecr_repository_url)
SHA=$(git rev-parse HEAD)
[[ "$SHA" =~ ^[a-f0-9]{40}$ ]] || { echo 'Expected an initialized Git repository with a commit' >&2; exit 1; }
REGISTRY="${IMAGE_REPOSITORY%%/*}"
# ECR image tags are immutable; pushing the same commit twice will fail.
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"
docker build -t "$IMAGE_REPOSITORY:$SHA" .
docker push "$IMAGE_REPOSITORY:$SHA"
printf 'Published IMAGE=%s:%s\n' "$IMAGE_REPOSITORY" "$SHA"
