#!/usr/bin/env bash
# Deploy Rustbucket to Minikube.
# Usage: infra/scripts/deploy-minikube.sh [--local-images]
#   --local-images  build the three images inside Minikube's Docker, so no registry is needed
set -euo pipefail

cd "$(dirname "$0")/../.."
NS=rustbucket
LOCAL_IMAGES=false

for arg in "$@"; do
  case "$arg" in
    --local-images) LOCAL_IMAGES=true ;;
    *) echo "Unknown option: $arg"; echo "Usage: $0 [--local-images]"; exit 2 ;;
  esac
done

for tool in minikube kubectl; do
  command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: $tool is not installed."; exit 1; }
done

if ! minikube status >/dev/null 2>&1; then
  echo "==> Starting Minikube"
  minikube start
fi

if [ "$LOCAL_IMAGES" = true ]; then
  # Image owner comes from the git remote (lowercase), unless OWNER is set in the environment.
  OWNER="${OWNER:-$(git remote get-url origin | sed -E 's#.*github\.com[:/]([^/]+)/.*#\1#' | tr '[:upper:]' '[:lower:]')}"
  echo "==> Building images inside Minikube's Docker (owner: $OWNER)"
  eval "$(minikube docker-env --shell bash)"
  for svc in backend worker frontend; do
    docker build -f "infra/docker/${svc}.Dockerfile" -t "ghcr.io/${OWNER}/rustbucket-${svc}:latest" .
  done
fi

echo "==> Applying namespace"
kubectl apply -f infra/k8s/00-namespace.yaml

if ! kubectl get secret rustbucket-secrets -n "$NS" >/dev/null 2>&1; then
  echo "ERROR: secret rustbucket-secrets is missing in namespace $NS."
  echo "Create it first (template: infra/k8s/examples/secret.example.yaml):"
  echo "  kubectl create secret generic rustbucket-secrets -n $NS \\"
  echo "    --from-literal=DATABASE_URL='...' --from-literal=GITHUB_TOKEN='...'"
  exit 1
fi

echo "==> Applying manifests"
# A finished Job cannot be updated in place, so remove the old one first.
kubectl delete job rustbucket-migrate -n "$NS" --ignore-not-found
kubectl apply -f infra/k8s/

echo "==> Waiting for deployments"
for d in redis backend worker frontend; do
  kubectl rollout status "deployment/$d" -n "$NS" --timeout=180s
done

echo "==> Frontend URL (keep this terminal open if it does not return on its own):"
minikube service frontend -n "$NS" --url
