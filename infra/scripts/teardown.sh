#!/usr/bin/env bash
# Remove everything Rustbucket created in the cluster.
# Usage: infra/scripts/teardown.sh
set -euo pipefail

NS=rustbucket

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl is not installed."; exit 1; }

echo "==> Deleting namespace $NS (all Rustbucket resources, including the secret)"
kubectl delete namespace "$NS" --ignore-not-found

echo "Done. Minikube itself is still running; stop it with: minikube stop"
