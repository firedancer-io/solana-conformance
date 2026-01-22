#!/bin/bash
#
# run_integration_tests.sh - Run solana-conformance integration tests
#
# Usage:
#   ./run_integration_tests.sh              # Run all tests
#   ./run_integration_tests.sh --debug      # Verbose output
#   ./run_integration_tests.sh --fast       # Skip slow tests
#   ./run_integration_tests.sh --help       # Show help
#
# Prerequisites:
#   - Virtual environment set up (source install.sh)
#   - Target .so files (see below)
#
# Target files can be provided via:
#   1. tests/targets/libsolfuzz_agave.so and tests/targets/libfd_exec_sol_compat.so
#   2. SOLFUZZ_TARGET and FIREDANCER_TARGET environment variables
#

set -e

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

show_help() {
    cat << EOF
run_integration_tests.sh - Run solana-conformance integration tests

Usage:
    ./run_integration_tests.sh [OPTIONS] [PYTEST_ARGS...]

Options:
    --help              Show this help message
    --debug             Run with verbose output (-s -vv)
    --fast              Skip tests marked as slow
    --parallel-only     Run only multiprocessing tests
    --single-only       Run only single-threaded tests

Prerequisites:
    1. Install solana-conformance:
         source install.sh

    2. Provide target .so files via ONE of:
         a) Place in tests/targets/:
              tests/targets/libsolfuzz_agave.so
              tests/targets/libfd_exec_sol_compat.so

         b) Set environment variables:
              export SOLFUZZ_TARGET=/path/to/libsolfuzz_agave.so
              export FIREDANCER_TARGET=/path/to/libfd_exec_sol_compat.so

Examples:
    ./run_integration_tests.sh                    # Run all tests
    ./run_integration_tests.sh --debug            # Verbose mode
    ./run_integration_tests.sh -k "test_execute"  # Run specific tests
    ./run_integration_tests.sh --fast -x          # Fast tests, stop on first failure
EOF
}

# Handle --help early
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}       Solana Conformance Integration Tests                ${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# =============================================================================
# Pre-flight checks
# =============================================================================
echo -e "${BLUE}==> Pre-flight checks${NC}"

# Check for virtual environment
if [ ! -f "$SCRIPT_DIR/test_suite_env/bin/activate" ]; then
    log_error "Virtual environment not found!"
    echo ""
    echo "    Please run the install script first:"
    echo "      source install.sh         # RHEL/CentOS"
    echo "      source install_ubuntu.sh  # Ubuntu"
    echo ""
    exit 1
fi

# Activate if not already activated
if [[ "$VIRTUAL_ENV" != *"test_suite_env"* ]]; then
    source "$SCRIPT_DIR/test_suite_env/bin/activate"
    log_info "Activated virtual environment"
else
    log_info "Virtual environment already active"
fi

# Check for pytest
if ! command -v pytest &>/dev/null; then
    log_error "pytest not found!"
    echo ""
    echo "    The virtual environment may be incomplete. Try:"
    echo "      pip install -e '.[dev]'"
    echo ""
    exit 1
fi
log_info "pytest found"

# Check for vendored dependencies
if [ ! -x "$SCRIPT_DIR/opt/bin/flatc" ]; then
    log_warn "Vendored dependencies not found, installing..."
    ./deps.sh
else
    log_info "Vendored dependencies present"
fi

echo ""

# =============================================================================
# Check for test targets
# =============================================================================
echo -e "${BLUE}==> Checking test targets${NC}"

LOCAL_SOLFUZZ="$SCRIPT_DIR/tests/targets/libsolfuzz_agave.so"
LOCAL_FIREDANCER="$SCRIPT_DIR/tests/targets/libfd_exec_sol_compat.so"

# solfuzz-agave target (required)
if [ -f "$LOCAL_SOLFUZZ" ]; then
    log_info "solfuzz-agave target: $LOCAL_SOLFUZZ"
    export SOLFUZZ_TARGET="$LOCAL_SOLFUZZ"
elif [ -n "$SOLFUZZ_TARGET" ] && [ -f "$SOLFUZZ_TARGET" ]; then
    log_info "solfuzz-agave target: $SOLFUZZ_TARGET (from env)"
else
    log_error "solfuzz-agave target not found!"
    echo ""
    echo "    Please provide the target via ONE of:"
    echo "      1. Copy to: tests/targets/libsolfuzz_agave.so"
    echo "      2. Set env: export SOLFUZZ_TARGET=/path/to/libsolfuzz_agave.so"
    echo ""
    echo "    Build it from solfuzz-agave repository:"
    echo "      git clone https://github.com/firedancer-io/solfuzz-agave"
    echo "      cd solfuzz-agave && cargo build --release"
    echo "      cp target/release/libsolfuzz_agave.so /path/to/solana-conformance/tests/targets/"
    echo ""
    echo "    Or set the SOLFUZZ_TARGET environment variable:"
    echo "      export SOLFUZZ_TARGET=/path/to/libsolfuzz_agave.so"
    echo ""
    exit 1
fi

# firedancer target (optional)
if [ -f "$LOCAL_FIREDANCER" ]; then
    log_info "firedancer target: $LOCAL_FIREDANCER"
    export FIREDANCER_TARGET="$LOCAL_FIREDANCER"
elif [ -n "$FIREDANCER_TARGET" ] && [ -f "$FIREDANCER_TARGET" ]; then
    log_info "firedancer target: $FIREDANCER_TARGET (from env)"
else
    log_warn "firedancer target not found (some tests will be skipped)"
    echo "    To run all tests, provide the target via:"
    echo "      1. Copy to: tests/targets/libfd_exec_sol_compat.so"
    echo "      2. Set env: export FIREDANCER_TARGET=/path/to/libfd_exec_sol_compat.so"
fi

echo ""

# =============================================================================
# Check for test data
# =============================================================================
echo -e "${BLUE}==> Checking test data${NC}"

TEST_DATA_DIR="$SCRIPT_DIR/tests/test_data"
if [ -d "$TEST_DATA_DIR/fixtures" ] && [ -n "$(ls -A "$TEST_DATA_DIR/fixtures" 2>/dev/null)" ]; then
    fixture_count=$(ls -1 "$TEST_DATA_DIR/fixtures" 2>/dev/null | wc -l)
    log_info "Test fixtures present ($fixture_count files)"
else
    log_warn "Test data not found, setting it up..."
    if python3 tests/setup_test_data.py; then
        log_info "Test data created"
    else
        log_error "Failed to setup test data!"
        echo ""
        echo "    Try running manually:"
        echo "      python3 tests/setup_test_data.py"
        echo ""
        exit 1
    fi
fi

echo ""

# =============================================================================
# Parse arguments
# =============================================================================
PYTEST_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            PYTEST_ARGS="$PYTEST_ARGS -s -vv"
            shift
            ;;
        --parallel-only)
            PYTEST_ARGS="$PYTEST_ARGS -m parallel"
            shift
            ;;
        --single-only|--single-threaded-only)
            PYTEST_ARGS="$PYTEST_ARGS -m debug"
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            shift
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# =============================================================================
# Run tests
# =============================================================================
echo -e "${BLUE}==> Running integration tests${NC}"
echo ""

# shellcheck disable=SC2086
if pytest tests/test_integration.py $PYTEST_ARGS; then
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}              All integration tests passed!                 ${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}              Some integration tests failed                  ${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Run with --debug for verbose output"
    echo "  - Check target .so files are compatible with your system"
    echo "  - Run: solana-conformance check-deps"
    echo ""
    exit 1
fi
