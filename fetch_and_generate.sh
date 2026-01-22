#!/usr/bin/env bash
#
# fetch_and_generate.sh - Generate Protobuf and FlatBuffers bindings from protosol
#
# Usage: ./fetch_and_generate.sh
#
# This script generates Python bindings from the protosol submodule:
#   - Protobuf bindings (using buf)
#   - FlatBuffers bindings (using flatc)
#
# Prerequisites:
#   - Run ./deps.sh to install buf and flatc
#   - protosol submodule initialized (git submodule update --init)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}==>${NC} $*"; }

# Output directories
PROTO_OUTPUT_DIR="src/test_suite/protos"
FBS_OUTPUT_DIR="src/test_suite/flatbuffers"

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       Protobuf & FlatBuffers Code Generation              ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# =============================================================================
# Pre-flight checks
# =============================================================================
log_step "Pre-flight checks..."

# Check for virtual environment
if [ ! -f "test_suite_env/bin/activate" ]; then
    log_error "Virtual environment not found!"
    echo ""
    echo "    Please run the install script first:"
    echo "      source install.sh       # RHEL/CentOS"
    echo "      source install_ubuntu.sh  # Ubuntu"
    echo ""
    exit 1
fi

source "test_suite_env/bin/activate"
log_info "Virtual environment activated"

# Check for git
if ! command -v git &>/dev/null; then
    log_error "git not found! Please install git."
    exit 1
fi

echo ""

# =============================================================================
# Check vendored tools (buf, flatc)
# =============================================================================
log_step "Checking vendored tools..."

BUF="$SCRIPT_DIR/opt/bin/buf"
FLATC="$SCRIPT_DIR/opt/bin/flatc"

# Use local cache directory for buf (don't pollute ~/.cache/buf)
export BUF_CACHE_DIR="$SCRIPT_DIR/opt/cache/buf"
mkdir -p "$BUF_CACHE_DIR"

missing_tools=()
[ ! -x "$BUF" ] && missing_tools+=("buf")
[ ! -x "$FLATC" ] && missing_tools+=("flatc")

if [ ${#missing_tools[@]} -gt 0 ]; then
    log_warn "Missing tools: ${missing_tools[*]}"
    echo ""
    if [ -x "$SCRIPT_DIR/deps.sh" ]; then
        read -p "Would you like to install them now using deps.sh? [Y/n] " -n 1 -r
        echo ""
        if [[ "$REPLY" =~ ^[Yy]$ ]] || [[ -z "$REPLY" ]]; then
            log_info "Running deps.sh..."
            "$SCRIPT_DIR/deps.sh" || {
                log_error "Failed to install dependencies via deps.sh"
                exit 1
            }
        else
            log_error "buf and flatc are required for code generation."
            echo "    To install, run: ./deps.sh"
            exit 1
        fi
    else
        log_error "deps.sh not found, cannot install tools automatically."
        echo "    Please run: ./deps.sh"
        exit 1
    fi
fi

# Verify tools are available
if [ ! -x "$BUF" ]; then
    log_error "buf not found at: $BUF"
    exit 1
fi
if [ ! -x "$FLATC" ]; then
    log_error "flatc not found at: $FLATC"
    exit 1
fi

log_info "buf: $("$BUF" --version 2>&1 | head -1)"
log_info "flatc: $("$FLATC" --version 2>&1)"

# Check for black (for formatting)
if ! command -v black &>/dev/null; then
    log_warn "black not found, generated files won't be formatted"
fi

echo ""

# =============================================================================
# Check protosol submodule
# =============================================================================
log_step "Checking protosol submodule..."

PROTOSOL_DIR="$SCRIPT_DIR/shlr/protosol"

if [ ! -d "$PROTOSOL_DIR/proto" ]; then
    log_warn "protosol submodule not initialized"
    log_info "Initializing git submodules..."
    git submodule update --init --recursive
    
    if [ ! -d "$PROTOSOL_DIR/proto" ]; then
        log_error "Failed to initialize protosol submodule!"
        echo ""
        echo "    Try manually:"
        echo "      git submodule update --init --recursive"
        echo ""
        exit 1
    fi
fi

PROTOSOL_VERSION="$(cd "$PROTOSOL_DIR" && git describe --tags 2>/dev/null || echo 'unknown')"
log_info "protosol: $PROTOSOL_DIR ($PROTOSOL_VERSION)"

echo ""

# =============================================================================
# Generate Protobuf bindings
# =============================================================================
log_step "Generating Protobuf bindings..."

# Check for proto files
if [ ! -d "$PROTOSOL_DIR/proto" ] || [ -z "$(ls -A $PROTOSOL_DIR/proto/*.proto 2>/dev/null)" ]; then
    log_error "No .proto files found in $PROTOSOL_DIR/proto/"
    exit 1
fi

# Ensure buf.gen.yaml exists
if [ ! -f "buf.gen.yaml" ]; then
    log_error "buf.gen.yaml not found!"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$PROTO_OUTPUT_DIR"

# Generate
if "$BUF" generate "$PROTOSOL_DIR/proto/"; then
    log_info "Protobuf code generated to $PROTO_OUTPUT_DIR/"
else
    log_error "buf generate failed!"
    echo "    Check buf.gen.yaml and $PROTOSOL_DIR/proto/ for issues."
    exit 1
fi

# Patch codegen'd imports (Python protobuf import fix)
touch "$PROTO_OUTPUT_DIR/__init__.py"
if sed -i.bak -E 's/^import ([a-zA-Z0-9_]+_pb2)/from . import \1/' "$PROTO_OUTPUT_DIR"/*_pb2.py 2>/dev/null; then
    rm -f "$PROTO_OUTPUT_DIR"/*.bak
    log_info "Patched protobuf imports"
fi

# Format with black
if command -v black &>/dev/null; then
    if black "$PROTO_OUTPUT_DIR"/*_pb2.py --quiet 2>/dev/null; then
        log_info "Formatted protobuf files"
    fi
fi

proto_count=$(ls -1 "$PROTO_OUTPUT_DIR"/*_pb2.py 2>/dev/null | wc -l)
echo "    Generated $proto_count protobuf files"

echo ""

# =============================================================================
# Generate FlatBuffers bindings
# =============================================================================
log_step "Generating FlatBuffers bindings..."

FBS_SRC_DIR="$PROTOSOL_DIR/flatbuffers"

if [ ! -d "$FBS_SRC_DIR" ]; then
    log_warn "No FlatBuffers schemas in protosol (skipping)"
    echo "    FlatBuffers schemas are available in protosol v3.0.0+"
else
    if ! ls "$FBS_SRC_DIR"/*.fbs &>/dev/null; then
        log_warn "No .fbs files found in $FBS_SRC_DIR (skipping)"
    else
        # Find schema files
        FBS_FILES=$(find "$FBS_SRC_DIR" -name "*.fbs" -type f | sort)
        FBS_COUNT=$(echo "$FBS_FILES" | wc -l)
        log_info "Found $FBS_COUNT schema files"
        
        # Clean previous generation
        if [ -d "$FBS_OUTPUT_DIR" ]; then
            rm -rf "$FBS_OUTPUT_DIR"
        fi
        mkdir -p "$FBS_OUTPUT_DIR"
        
        # Generate Python bindings
        ABS_FBS_OUTPUT_DIR="$SCRIPT_DIR/$FBS_OUTPUT_DIR"
        pushd "$FBS_SRC_DIR" >/dev/null
        
        if "$FLATC" --python -o "$ABS_FBS_OUTPUT_DIR" *.fbs; then
            log_info "FlatBuffers code generated to $FBS_OUTPUT_DIR/"
        else
            log_error "flatc failed to generate code!"
            popd >/dev/null
            exit 1
        fi
        
        popd >/dev/null
        
        # Create Python package structure (__init__.py files)
        find "$FBS_OUTPUT_DIR" -type d | while read -r dir; do
            init_file="$dir/__init__.py"
            if [ ! -f "$init_file" ]; then
                echo "# Auto-generated FlatBuffers package" > "$init_file"
            fi
        done
        log_info "Created __init__.py files"
        
        fbs_py_count=$(find "$FBS_OUTPUT_DIR" -name "*.py" -type f | wc -l)
        echo "    Generated $fbs_py_count Python files"
    fi
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}              Code Generation Complete!                     ${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Generated files:"
echo "  Protobuf:    $PROTO_OUTPUT_DIR/ ($proto_count files)"
if [ -d "$FBS_OUTPUT_DIR" ]; then
    fbs_py_count=$(find "$FBS_OUTPUT_DIR" -name "*.py" -type f 2>/dev/null | wc -l)
    echo "  FlatBuffers: $FBS_OUTPUT_DIR/ ($fbs_py_count files)"
fi
echo ""
echo "Usage:"
echo "  # Protobuf"
echo "  from test_suite.protos import invoke_pb2"
echo ""
echo "  # FlatBuffers"
echo "  from test_suite.flatbuffers_utils import FixtureLoader"
echo "  loader = FixtureLoader(Path('fixture.fix'))"
echo ""
