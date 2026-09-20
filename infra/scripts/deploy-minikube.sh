#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="rustbucket"

echo "==> Starting Minikube..."
minikube start

echo "==> Creating namespace..."
kubectl apply -f infra/k8s/00-namespace.yaml

echo "==> Creating runtime secret..."
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  echo "Set it before running this script."
  exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: GITHUB_TOKEN is not set."
  exit 1
fi

kubectl -n "$NAMESPACE" create secret generic rustbucket-secrets \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=GITHUB_TOKEN="$GITHUB_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Applying ConfigMap..."
kubectl apply -f infra/k8s/10-configmap.yaml

echo "==> Deploying Redis..."
kubectl apply -f infra/k8s/20-redis.yaml

echo "==> Waiting for Redis..."
kubectl -n "$NAMESPACE" rollout status deployment/redis --timeout=120s

echo "==> Deploying backend..."
kubectl apply -f infra/k8s/40-backend.yaml

echo "==> Deploying worker..."
kubectl apply -f infra/k8s/50-worker.yaml

echo "==> Deploying frontend..."
kubectl apply -f infra/k8s/60-frontend.yaml

echo "==> Running database migration..."
kubectl apply -f infra/k8s/30-migrate-job.yaml

echo "==> Deployment complete."
kubectl -n "$NAMESPACE" get pods
kubectl -n "$NAMESPACE" get services