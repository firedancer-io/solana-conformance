#!/bin/bash
#
# exec_it.sh - Execute a fixture through agave or firedancer target
#
# Usage: ./exec_it.sh <fixture_path> [a|f]
#
# Arguments:
#   fixture_path  Path to the context/fixture file
#   a             Use Agave target (SOL_TARGET or SOLFUZZ_TARGET)
#   f             Use Firedancer target (FD_TARGET or FIREDANCER_TARGET) [default]
#
# Examples:
#   ./exec_it.sh fixture.fix a    # Execute through Agave
#   ./exec_it.sh fixture.fix f    # Execute through Firedancer
#   ./exec_it.sh fixture.fix      # Execute through Firedancer (default)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate virtual environment if not already active
if [[ "$VIRTUAL_ENV" != *"test_suite_env"* ]]; then
    if [ -f "$SCRIPT_DIR/test_suite_env/bin/activate" ]; then
        source "$SCRIPT_DIR/test_suite_env/bin/activate"
    else
        echo "Error: Virtual environment not found."
        echo "Run: source install.sh"
        exit 1
    fi
fi

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <fixture_path> [a|f]"
    echo ""
    echo "Arguments:"
    echo "  fixture_path  Path to the context/fixture file"
    echo "  a             Use Agave target"
    echo "  f             Use Firedancer target [default]"
    echo ""
    echo "Environment variables:"
    echo "  SOL_TARGET or SOLFUZZ_TARGET - Path to Agave .so"
    echo "  FD_TARGET or FIREDANCER_TARGET - Path to Firedancer .so"
    exit 1
fi

FIXTURE_PATH="$1"

# Select target
if [ "$2" = "a" ]; then
    echo "EXECUTING THROUGH AGAVE..."
    TARGET="${SOL_TARGET:-$SOLFUZZ_TARGET}"
    if [ -z "$TARGET" ]; then
        echo "Error: Agave target not set."
        echo "Set SOL_TARGET or SOLFUZZ_TARGET environment variable."
        exit 1
    fi
else
    echo "EXECUTING THROUGH FIREDANCER..."
    TARGET="${FD_TARGET:-$FIREDANCER_TARGET}"
    if [ -z "$TARGET" ]; then
        echo "Error: Firedancer target not set."
        echo "Set FD_TARGET or FIREDANCER_TARGET environment variable."
        exit 1
    fi
fi

# Check target exists
if [ ! -f "$TARGET" ]; then
    echo "Error: Target not found: $TARGET"
    exit 1
fi

# Check fixture exists
if [ ! -f "$FIXTURE_PATH" ]; then
    echo "Error: Fixture not found: $FIXTURE_PATH"
    exit 1
fi

solana-conformance exec-instr -t "$TARGET" -i "$FIXTURE_PATH"
