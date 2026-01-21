#!/usr/bin/env bash
set -euo pipefail

# Generate Python FlatBuffers bindings from protosol .fbs schemas
#
# This script:
# 1. Ensures flatc is available
# 2. Fetches/updates protosol (same repo as protobufs)
# 3. Generates Python FlatBuffers bindings
# 4. Creates necessary __init__.py files

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "test_suite_env/bin/activate" ]; then
    source "test_suite_env/bin/activate"
fi

# v3.0.0+ includes FlatBuffers schemas
PROTO_VERSION="${PROTO_VERSION:-v3.0.0}"
FBS_OUTPUT_DIR="src/test_suite/flatbuffers"

echo "=== FlatBuffers Code Generation ==="
echo "protosol version: ${PROTO_VERSION}"
echo "output directory: ${FBS_OUTPUT_DIR}"
echo ""

# Step 1: Ensure flatc is available
echo "Step 1: Checking for flatc..."

# Run ensure_flatc.sh and capture FLATC_PATH
FLATC=""
if FLATC_PATH=$("./ensure_flatc.sh" 2>&1 | grep "Found flatc at:" | sed 's/Found flatc at: //'); then
    FLATC="$FLATC_PATH"
fi

# Fallback: try common locations
if [ -z "$FLATC" ] || [ ! -x "$FLATC" ]; then
    for candidate in \
        "${SOLFUZZ_DIR:-/data/$USER/solfuzz}/bin/flatc" \
        "/data/$USER/solfuzz/bin/flatc" \
        "/data/$USER/repos/solfuzz/bin/flatc" \
        "$HOME/solfuzz/bin/flatc" \
        "$(command -v flatc 2>/dev/null)" \
        "$HOME/.local/bin/flatc"
    do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            FLATC="$candidate"
            break
        fi
    done
fi

if [ -z "$FLATC" ] || [ ! -x "$FLATC" ]; then
    echo "ERROR: flatc not found. Run ./ensure_flatc.sh first or set SOLFUZZ_DIR."
    exit 1
fi
echo "Using flatc: $FLATC"
"$FLATC" --version
echo ""

# Step 2: Fetch/update protosol
echo "Step 2: Fetching protosol..."
if [ ! -d protosol ]; then
    git clone --depth=1 --branch "$PROTO_VERSION" https://github.com/firedancer-io/protosol.git
else
    cd protosol
    git fetch --tags
    git checkout "$PROTO_VERSION"
    cd ..
fi
echo ""

# Step 3: Generate FlatBuffers Python bindings
echo "Step 3: Generating Python FlatBuffers bindings..."

# Clean previous generation
rm -rf "$FBS_OUTPUT_DIR"
mkdir -p "$FBS_OUTPUT_DIR"

# Find FlatBuffers source directory
# Try multiple locations (protosol may have fbs in different versions)
FBS_SRC_DIR=""
for candidate in \
    "protosol/flatbuffers" \
    "${SOLFUZZ_DIR:-/data/$USER/solfuzz}/protosol/flatbuffers" \
    "/data/$USER/solfuzz/protosol/flatbuffers" \
    "/data/$USER/repos/solfuzz/protosol/flatbuffers" \
    "$HOME/solfuzz/protosol/flatbuffers"
do
    if [ -d "$candidate" ] && ls "$candidate"/*.fbs &>/dev/null; then
        FBS_SRC_DIR="$candidate"
        break
    fi
done

if [ -z "$FBS_SRC_DIR" ]; then
    echo "ERROR: FlatBuffers source directory not found."
    echo "Tried: protosol/flatbuffers, \$SOLFUZZ_DIR/protosol/flatbuffers"
    echo ""
    echo "Either:"
    echo "  1. Use a protosol version that includes FlatBuffers schemas"
    echo "  2. Set SOLFUZZ_DIR to point to solfuzz (which has protosol with fbs)"
    exit 1
fi
echo "Using FlatBuffers schemas from: $FBS_SRC_DIR"

# Find all .fbs files
FBS_FILES=$(find "$FBS_SRC_DIR" -name "*.fbs" -type f | sort)
if [ -z "$FBS_FILES" ]; then
    echo "ERROR: No .fbs files found in $FBS_SRC_DIR"
    exit 1
fi

echo "Found FlatBuffers schemas:"
for f in $FBS_FILES; do
    echo "  - $f"
done
echo ""

# Generate Python bindings
# Note: flatc generates into a namespace-based directory structure
# Use absolute paths to handle both relative and absolute FBS_SRC_DIR
ABS_FBS_OUTPUT_DIR="$(cd "$SCRIPT_DIR" && pwd)/$FBS_OUTPUT_DIR"
pushd "$FBS_SRC_DIR" >/dev/null
"$FLATC" --python -o "$ABS_FBS_OUTPUT_DIR" *.fbs
popd >/dev/null

echo ""

# Step 4: Create __init__.py files for proper Python packaging
echo "Step 4: Creating Python package structure..."

# Find all directories and create __init__.py
find "$FBS_OUTPUT_DIR" -type d | while read -r dir; do
    init_file="$dir/__init__.py"
    if [ ! -f "$init_file" ]; then
        echo "# Auto-generated FlatBuffers package" > "$init_file"
    fi
done

# List generated files
echo ""
echo "Generated files:"
find "$FBS_OUTPUT_DIR" -name "*.py" -type f | sort

echo ""
echo "=== FlatBuffers generation complete ==="
echo ""
echo "To use in Python:"
echo "  from test_suite.flatbuffers.org.solana.sealevel.v2.ELFLoaderFixture import ELFLoaderFixture"
echo ""
echo "Or use the unified loader:"
echo "  from test_suite.flatbuffers_utils import FixtureLoader"
echo "  loader = FixtureLoader(Path('fixture.fix'))"

