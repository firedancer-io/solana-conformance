#!/usr/bin/env bash
set -euo pipefail

PINNED=$(grep "protobuf==" pyproject.toml | grep -oP "\d+\.\d+\.\d+")
if [ -z "$PINNED" ]; then
  echo "WARNING: Could not find protobuf version pin in pyproject.toml"
  exit 0
fi

FAILED=0
for f in src/test_suite/protos/*_pb2.py; do
  GENVER=$(grep "Protobuf Python Version:" "$f" 2>/dev/null | grep -oP "\d+\.\d+\.\d+" || true)
  if [ -n "$GENVER" ] && [ "$GENVER" != "$PINNED" ]; then
    echo "ERROR: $f was generated for protobuf $GENVER but pyproject.toml pins $PINNED"
    FAILED=1
  fi
done

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "Fix: update buf.gen.yaml plugin version, then run ./fetch_and_generate.sh"
  exit 1
fi
