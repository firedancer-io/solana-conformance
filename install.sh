#!/bin/bash
# Install solana-conformance Python environment and dependencies
#
# Usage: source install.sh
#
# This script will:
# 1. Install system dependencies (gcc-toolset-12)
# 2. Install vendored dependencies (flatc)
# 3. Create Python virtual environment
# 4. Install Python packages
# 5. Generate protobuf/flatbuffers bindings

set -e

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

# Ensure we're in the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}       solana-conformance Installation (RHEL/Rocky)        ${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# =============================================================================
# Pre-flight checks
# =============================================================================
log_step "Running pre-flight checks..."

# Check we're on RHEL/CentOS
if [ ! -f /etc/redhat-release ]; then
    log_warn "This script is designed for RHEL/CentOS. For Ubuntu, use install_ubuntu.sh"
    echo "    Detected OS: $(grep PRETTY_NAME /etc/os-release 2>/dev/null | cut -d'"' -f2 || uname -s)"
    read -p "    Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for Python 3.11
if ! command -v python3.11 &>/dev/null; then
    log_error "Python 3.11 not found!"
    echo ""
    echo "    Please install Python 3.11 first:"
    echo "      sudo dnf install python3.11 python3.11-devel"
    echo ""
    exit 1
fi
log_info "Python 3.11 found: $(python3.11 --version)"

# Check for git
if ! command -v git &>/dev/null; then
    log_error "git not found!"
    echo "    Please install git: sudo dnf install git"
    exit 1
fi
log_info "git found: $(git --version | head -1)"

# Check for curl (needed for deps.sh)
if ! command -v curl &>/dev/null; then
    log_error "curl not found!"
    echo "    Please install curl: sudo dnf install curl"
    exit 1
fi
log_info "curl found"

echo ""

# =============================================================================
# Install system dependencies
# =============================================================================
log_step "Installing system dependencies..."

if sudo dnf install -y gcc-toolset-12 2>/dev/null; then
    log_info "gcc-toolset-12 installed"
else
    log_warn "Could not install gcc-toolset-12 (may already be installed or require manual setup)"
fi

if [ -f /opt/rh/gcc-toolset-12/enable ]; then
    source /opt/rh/gcc-toolset-12/enable
    log_info "gcc-toolset-12 enabled"
else
    log_warn "gcc-toolset-12 enable script not found, using system compiler"
fi

# Python dev headers
if sudo dnf install -y python3.11-devel 2>/dev/null; then
    log_info "python3.11-devel installed"
else
    log_warn "Could not install python3.11-devel (may already be installed)"
fi

# Build tools for deps.sh
if sudo dnf install -y cmake make gcc-c++ 2>/dev/null; then
    log_info "cmake, make, gcc-c++ installed"
else
    log_warn "Could not install build tools (may already be installed)"
fi

echo ""

# =============================================================================
# Initialize submodules and build vendored dependencies
# =============================================================================
log_step "Initializing git submodules..."
git submodule update --init --recursive
log_info "Submodules initialized"

log_step "Building vendored dependencies (flatc)..."

if [ -x "./deps.sh" ]; then
    ./deps.sh
else
    log_error "deps.sh not found or not executable!"
    echo "    Make sure you're in the solana-conformance directory"
    exit 1
fi

echo ""

# =============================================================================
# Create Python virtual environment
# =============================================================================
log_step "Setting up Python virtual environment..."

if [ -d "test_suite_env" ]; then
    log_info "Virtual environment already exists, reusing"
else
    python3.11 -m venv test_suite_env
    log_info "Created virtual environment: test_suite_env/"
fi

source test_suite_env/bin/activate
log_info "Activated virtual environment"

echo ""

# =============================================================================
# Install Python packages
# =============================================================================
log_step "Installing Python packages..."

# Upgrade pip first
pip install --upgrade pip --quiet
log_info "pip upgraded"

# Install the package with all dependencies
if pip install -e ".[dev,octane]"; then
    log_info "solana-conformance installed with dev and octane dependencies"
else
    log_error "Failed to install Python packages!"
    echo ""
    echo "    Try running manually:"
    echo "      source test_suite_env/bin/activate"
    echo "      pip install -e '.[dev,octane]'"
    echo ""
    exit 1
fi

echo ""

# =============================================================================
# Install pre-commit hooks (optional)
# =============================================================================
log_step "Setting up pre-commit hooks..."

if pre-commit install 2>/dev/null; then
    log_info "pre-commit hooks installed"
else
    log_warn "pre-commit hooks not installed"
    echo "    This may be because core.hooksPath is set in your git config."
    echo "    To fix: git config --unset-all core.hooksPath"
    echo "    This is optional - solana-conformance will work without pre-commit hooks."
fi

echo ""

# =============================================================================
# Generate protobuf/flatbuffers bindings
# =============================================================================
log_step "Checking code generation..."

if [ -d "src/test_suite/protos" ] && [ -n "$(ls -A src/test_suite/protos/*.py 2>/dev/null)" ]; then
    log_info "Protobuf bindings already exist"
else
    log_info "Generating protobuf/flatbuffers bindings..."
    if [ -x "./fetch_and_generate.sh" ]; then
        if ./fetch_and_generate.sh; then
            log_info "Code generation complete"
        else
            log_warn "Code generation had issues - you may need to run ./fetch_and_generate.sh manually"
        fi
    else
        log_warn "fetch_and_generate.sh not found, skipping code generation"
        echo "    Run ./fetch_and_generate.sh manually to generate protobuf bindings"
    fi
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}              Installation Complete!                        ${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  To activate the environment in a new shell:"
echo -e "    ${BLUE}source test_suite_env/bin/activate${NC}"
echo ""
echo "  To verify installation:"
echo -e "    ${BLUE}solana-conformance --help${NC}"
echo -e "    ${BLUE}solana-conformance check-deps${NC}"
echo ""
echo "  To run tests (requires target .so files):"
echo -e "    ${BLUE}./run_integration_tests.sh${NC}"
echo ""
