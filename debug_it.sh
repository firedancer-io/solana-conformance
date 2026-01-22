#!/bin/bash
#
# debug_it.sh - Debug a fixture with GDB
#
# Usage: ./debug_it.sh <fixture_path> <target_so>
#
# Example:
#   ./debug_it.sh path/to/fixture.fix $FD_TARGET
#   ./debug_it.sh path/to/fixture.fix /path/to/libfd_exec_sol_compat.so
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <fixture_path> <target_so>"
    echo ""
    echo "Arguments:"
    echo "  fixture_path  Path to the fixture file (.fix, .elfctx, etc.)"
    echo "  target_so     Path to the target .so file"
    echo ""
    echo "Examples:"
    echo "  $0 fixtures/bug.fix \$FD_TARGET"
    echo "  $0 fixtures/bug.fix /path/to/libfd_exec_sol_compat.so"
    exit 1
fi

FIXTURE_PATH="$1"
TARGET_PATH="$2"

# Convert fixture path to absolute if relative
if [[ "$FIXTURE_PATH" != /* ]]; then
    # If it doesn't exist relative to CWD, try relative to original CWD
    if [ ! -f "$FIXTURE_PATH" ] && [ -n "$OLDPWD" ] && [ -f "$OLDPWD/$FIXTURE_PATH" ]; then
        FIXTURE_PATH="$OLDPWD/$FIXTURE_PATH"
    fi
fi

# Check fixture exists
if [ ! -f "$FIXTURE_PATH" ]; then
    echo "Error: Fixture not found: $FIXTURE_PATH"
    exit 1
fi

# Check target exists
if [ ! -f "$TARGET_PATH" ]; then
    echo "Error: Target .so not found: $TARGET_PATH"
    echo ""
    echo "Set FIREDANCER_TARGET or SOLFUZZ_TARGET environment variable,"
    echo "or provide the full path to the .so file."
    exit 1
fi

# Activate virtual environment
if [ -f "$SCRIPT_DIR/test_suite_env/bin/activate" ]; then
    source "$SCRIPT_DIR/test_suite_env/bin/activate"
else
    echo "Error: Virtual environment not found at $SCRIPT_DIR/test_suite_env"
    echo "Run: source install.sh"
    exit 1
fi

# Create output directory
OUTPUT_DIR="$SCRIPT_DIR/scratch/debug_output"
mkdir -p "$OUTPUT_DIR"

# Check for debug.gdb
GDB_SCRIPT="$SCRIPT_DIR/debug.gdb"
GDB_ARGS=""
if [ -f "$GDB_SCRIPT" ]; then
    GDB_ARGS="-x $GDB_SCRIPT"
fi

echo "Debugging fixture: $FIXTURE_PATH"
echo "Using target: $TARGET_PATH"
echo "Output dir: $OUTPUT_DIR"
echo ""

# Run GDB
gdb $GDB_ARGS --args python3.11 -m test_suite.test_suite exec-fixtures \
    -i "$FIXTURE_PATH" \
    -t "$TARGET_PATH" \
    -o "$OUTPUT_DIR" \
    --debug-mode
