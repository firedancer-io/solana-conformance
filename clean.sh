#!/bin/bash
#
# clean.sh - Clean up solana-conformance installation
#
# Usage: source clean.sh
#
# This removes:
#   - Python virtual environment (test_suite_env/)
#   - Vendored dependencies (opt/)
#   - Generated protobuf/flatbuffers bindings
#   - Fetched protosol repository
#   - Build artifacts
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Cleaning solana-conformance..."

# Deactivate virtual environment if active
if [[ "$VIRTUAL_ENV" == *"test_suite_env"* ]]; then
    deactivate 2>/dev/null || true
    echo "  Deactivated virtual environment"
fi

# Remove virtual environment
if [ -d "test_suite_env" ]; then
    rm -rf test_suite_env
    echo "  Removed test_suite_env/"
fi

# Remove vendored dependencies
if [ -d "opt" ]; then
    rm -rf opt
    echo "  Removed opt/"
fi

# Remove generated bindings
if [ -d "src/test_suite/protos" ]; then
    rm -rf src/test_suite/protos
    echo "  Removed src/test_suite/protos/"
fi

if [ -d "src/test_suite/flatbuffers" ]; then
    rm -rf src/test_suite/flatbuffers
    echo "  Removed src/test_suite/flatbuffers/"
fi

# Remove fetched protosol (legacy location - now a submodule in shlr/protosol/)
if [ -d "protosol" ]; then
    rm -rf protosol
    echo "  Removed protosol/ (legacy location)"
fi

# Note: shlr/protosol is a git submodule and should NOT be deleted
# To fully reset submodules: git submodule deinit --all -f

# Remove any compiled .so files in src
if ls src/*.so 2>/dev/null; then
    rm -f src/*.so
    echo "  Removed src/*.so"
fi

# Remove egg-info
if ls src/*.egg-info 2>/dev/null; then
    rm -rf src/*.egg-info
    echo "  Removed src/*.egg-info"
fi

# Clean impl submodule if it exists
if [ -d "impl" ] && [ -f "impl/Makefile" ]; then
    make -C impl clean 2>/dev/null || true
    echo "  Cleaned impl/"
fi

# Note: We don't deinit shlr/ submodules by default since they're needed for building.
# To fully clean submodules, run: git submodule deinit --all -f

echo ""
echo "Clean complete. To reinstall:"
echo "  source install.sh       # RHEL/CentOS"
echo "  source install_ubuntu.sh  # Ubuntu"
