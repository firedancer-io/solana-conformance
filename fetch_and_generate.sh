#!/usr/bin/env sh

# Fetch protosol
if [ ! -d protosol ]; then
    git clone --depth=1 -b runtime_fuzz_v2_updates -q https://github.com/firedancer-io/protosol.git
else
    cd protosol
    git pull -q
    cd ..
fi

# Generate protobuf files with protoc
protoc --python_out=src/test_suite --proto_path=protosol/proto --proto_path=protosol/proto_v2 protosol/proto/*.proto protosol/proto_v2/*.proto
protol --in-place --python-out=src/test_suite protoc --proto-path=protosol/proto protosol/proto/*.proto
protol --in-place --python-out=src/test_suite protoc --proto-path=protosol/proto_v2 protosol/proto_v2/*.proto

# Format generated files with black to avoid false positive git diffs
black src/test_suite/*_pb2.py
