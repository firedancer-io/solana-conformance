#!/bin/bash
# Install solana-conformance Python environment and dependencies

set -e

# Install system dependencies
sudo dnf install -y gcc-toolset-12 || true
source /opt/rh/gcc-toolset-12/enable

# Create and activate virtual environment
python3.11 -m venv test_suite_env
source test_suite_env/bin/activate

# Install Python dev headers
sudo dnf install -y python3.11-devel || true

# Install package in editable mode with dev and octane dependencies
pip install -e ".[dev,octane]"

# Install pre-commit hooks (optional, may fail if core.hooksPath is set)
pre-commit install || echo "WARNING: pre-commit hooks not installed (you may have core.hooksPath set)"

# Generate protobuf/flatbuffers bindings if missing
if [ ! -d "src/test_suite/protos" ] || [ -z "$(ls -A src/test_suite/protos/*.py 2>/dev/null)" ]; then
    echo "Protobuf bindings missing, generating..."
    if [ -f "fetch_and_generate.sh" ]; then
        ./fetch_and_generate.sh
    else
        echo "WARNING: fetch_and_generate.sh not found, protos may be missing"
    fi
fi

echo "solana-conformance installed successfully"
