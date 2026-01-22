#!/bin/bash
# Install solana-conformance on Ubuntu
#
# Usage: source install_ubuntu.sh
#
# This script will:
# 1. Install system dependencies (gcc-12, Python 3.11)
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
echo -e "${GREEN}       solana-conformance Installation (Ubuntu)            ${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# =============================================================================
# Pre-flight checks
# =============================================================================
log_step "Running pre-flight checks..."

# Check we're on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    log_warn "This script is designed for Ubuntu/Debian. For RHEL/CentOS, use install.sh"
    echo "    Detected OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || uname -s)"
    read -p "    Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for git
if ! command -v git &>/dev/null; then
    log_error "git not found!"
    echo "    Please install git: sudo apt install git"
    exit 1
fi
log_info "git found: $(git --version | head -1)"

# Check for curl (needed for deps.sh)
if ! command -v curl &>/dev/null; then
    log_error "curl not found!"
    echo "    Please install curl: sudo apt install curl"
    exit 1
fi
log_info "curl found"

echo ""

# =============================================================================
# Install system dependencies
# =============================================================================
log_step "Installing system dependencies..."

# Build essentials
if sudo apt install -y build-essential software-properties-common; then
    log_info "build-essential installed"
else
    log_warn "Could not install build-essential"
fi

# GCC 12
log_info "Setting up GCC 12..."
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test 2>/dev/null || true
sudo apt update -qq

if sudo apt install -y gcc-12 g++-12; then
    log_info "gcc-12 and g++-12 installed"
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 20 2>/dev/null || true
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 20 2>/dev/null || true
else
    log_warn "Could not install gcc-12, using system default"
fi

# Python 3.11
if ! command -v python3.11 &>/dev/null; then
    log_info "Installing Python 3.11..."
    if sudo apt install -y python3.11 python3.11-dev python3.11-venv; then
        log_info "Python 3.11 installed"
    else
        log_error "Failed to install Python 3.11!"
        echo ""
        echo "    Try adding the deadsnakes PPA:"
        echo "      sudo add-apt-repository ppa:deadsnakes/ppa"
        echo "      sudo apt update"
        echo "      sudo apt install python3.11 python3.11-dev python3.11-venv"
        echo ""
        exit 1
    fi
else
    log_info "Python 3.11 already installed: $(python3.11 --version)"
    # Make sure dev and venv packages are installed
    sudo apt install -y python3.11-dev python3.11-venv 2>/dev/null || true
fi

# Build tools for deps.sh
if sudo apt install -y cmake make g++ 2>/dev/null; then
    log_info "cmake, make, g++ installed"
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
