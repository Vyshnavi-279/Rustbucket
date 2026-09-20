#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="rustbucket"

echo "==> Checking Kubernetes resources..."

kubectl -n "$NAMESPACE" get pods
kubectl -n "$NAMESPACE" get services

echo "==> Checking backend..."
kubectl -n "$NAMESPACE" run smoke-test \
  --rm \
  -i \
  --restart=Never \
  --image=curlimages/curl:8.10.1 \
  -- curl -fsS http://backend:8000/health

echo "==> Backend health check passed."

echo "==> Checking frontend service..."
kubectl -n "$NAMESPACE" run frontend-smoke-test \
  --rm \
  -i \
  --restart=Never \
  --image=curlimages/curl:8.10.1 \
  -- curl -fsS http://frontend:80/

echo "==> Frontend health check passed."
echo "==> Smoke test completed successfully."