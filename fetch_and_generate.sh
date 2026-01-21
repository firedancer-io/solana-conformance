#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/test_suite_env/bin/activate"

# v3.0.0+ includes FlatBuffers schemas in addition to Protobuf
PROTO_VERSION="${PROTO_VERSION:-v3.0.0}"

# Fetch protosol
if [ ! -d protosol ]; then
    git clone --depth=1 --branch "$PROTO_VERSION" https://github.com/firedancer-io/protosol.git
else
    cd protosol
    git fetch --tags
    git checkout "$PROTO_VERSION"
    cd ..
fi

# =============================================================================
# Generate Protobuf files with buf 
# =============================================================================
echo "=== Generating Protobuf bindings ==="
./ensure_buf.sh
buf generate ./protosol/proto/

# Patch codegen'd imports
touch ./src/test_suite/protos/__init__.py
sed -i.bak -E 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' src/test_suite/protos/*_pb2.py && rm src/test_suite/protos/*.bak

# Format generated files with black to avoid false positive git diffs
black src/test_suite/protos/*_pb2.py

# =============================================================================
# Generate FlatBuffers bindings (if .fbs files exist)
# =============================================================================
if [ -d "protosol/flatbuffers" ] && ls protosol/flatbuffers/*.fbs &>/dev/null; then
    echo ""
    echo "=== Generating FlatBuffers bindings ==="
    ./generate_flatbuffers.sh
else
    echo ""
    echo "=== Skipping FlatBuffers (no .fbs files in protosol) ==="
fi

echo ""
echo "=== Code generation complete ==="
