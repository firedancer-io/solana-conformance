#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/test_suite_env/bin/activate"

PROTO_VERSION="${PROTO_VERSION:-v1.0.4}"

# Fetch protosol
if [ ! -d protosol ]; then
    git clone --depth=1 --branch "$PROTO_VERSION" https://github.com/firedancer-io/protosol.git
else
    cd protosol
    git fetch --tags
    git checkout "$PROTO_VERSION"
    cd ..
fi

# Generate protobuf files with buf 
./ensure_buf.sh
buf generate ./protosol/proto/

# Patch codegen'd imports
touch ./src/test_suite/protos/__init__.py
sed -i.bak -E 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' src/test_suite/protos/*_pb2.py && rm src/test_suite/protos/*.bak

# Format generated files with black to avoid false positive git diffs
black src/test_suite/protos/*_pb2.py
