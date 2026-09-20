#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="rustbucket"

echo "==> Removing Rustbucket resources..."

kubectl delete namespace "$NAMESPACE" --ignore-not-found=true

echo "==> Rustbucket resources removed."