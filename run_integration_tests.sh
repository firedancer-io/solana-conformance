#!/bin/bash
# Integration test runner for solana-conformance
# Can be run locally or in CI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Solana Conformance Integration Tests ===${NC}\n"

# Check for test targets
SCRIPT_DIR="$(dirname "$0")"
LOCAL_SOLFUZZ="$SCRIPT_DIR/tests/targets/libsolfuzz_agave.so"
LOCAL_FIREDANCER="$SCRIPT_DIR/tests/targets/libfd_exec_sol_compat.so"

# Use local targets if they exist, otherwise require environment variables
if [ -f "$LOCAL_SOLFUZZ" ]; then
    echo -e "${GREEN}Using local solfuzz-agave target: $LOCAL_SOLFUZZ${NC}"
    export SOLFUZZ_TARGET="$LOCAL_SOLFUZZ"
elif [ -n "$SOLFUZZ_TARGET" ] && [ -f "$SOLFUZZ_TARGET" ]; then
    echo -e "${GREEN}Using SOLFUZZ_TARGET: $SOLFUZZ_TARGET${NC}"
else
    echo -e "${RED}Error: solfuzz-agave target not found${NC}"
    echo "Either:"
    echo "  1. Place libsolfuzz_agave.so in tests/targets/"
    echo "  2. Set SOLFUZZ_TARGET environment variable"
    exit 1
fi

if [ -f "$LOCAL_FIREDANCER" ]; then
    echo -e "${GREEN}Using local firedancer target: $LOCAL_FIREDANCER${NC}"
    export FIREDANCER_TARGET="$LOCAL_FIREDANCER"
elif [ -n "$FIREDANCER_TARGET" ] && [ -f "$FIREDANCER_TARGET" ]; then
    echo -e "${GREEN}Using FIREDANCER_TARGET: $FIREDANCER_TARGET${NC}"
else
    echo -e "${YELLOW}Warning: firedancer target not found${NC}"
    echo "Some tests will be skipped. To run all tests:"
    echo "  1. Place libfd_exec_sol_compat.so in tests/targets/, or"
    echo "  2. Set FIREDANCER_TARGET environment variable"
fi

echo ""

# Check for test data
TEST_DATA_DIR="$(dirname "$0")/tests/test_data"
if [ ! -d "$TEST_DATA_DIR/fixtures" ] || [ -z "$(ls -A "$TEST_DATA_DIR/fixtures" 2>/dev/null)" ]; then
    echo -e "${YELLOW}Test data not found, setting it up...${NC}"
    python3 tests/setup_test_data.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to setup test data${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Running integration tests...${NC}\n"

# Parse arguments
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
        --single-threaded-only)
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

# Run pytest
pytest tests/test_integration.py $PYTEST_ARGS

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=== All integration tests passed! ===${NC}"
    exit 0
else
    echo -e "\n${RED}=== Some integration tests failed ===${NC}"
    exit 1
fi

