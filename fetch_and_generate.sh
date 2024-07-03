#!/usr/bin/env sh

# Fetch protosol
if [ ! -d protosol ]; then
    git clone --depth=1 -q https://github.com/firedancer-io/protosol.git
else
    cd protosol
    git pull -q
    cd ..
fi

# Generate protobuf files with protoc
protoc --python_out=src/test_suite --proto_path=protosol/proto protosol/proto/*.proto
protol --in-place --python-out=src/test_suite protoc --proto-path=protosol/proto protosol/proto/*.proto

# Format generated files with black to avoid false positive git diffs
black src/test_suite/*_pb2.py
