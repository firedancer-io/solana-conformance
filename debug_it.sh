#!/bin/bash

# usage: ./debug_it.sh <ctx_file> [a]
# arg 1 is ctx file
# arg 2 is optional, if 'a' then use agave target, otherwise use fd target
# example: ./debug_it.sh <ctx_file> a

# make sure your python venv is activated: source solana-conformance/test_suite_env/bin/activate

if [ "$2" = "a" ]; then
    echo "DEBUGGING THROUGH AGAVE..."
    TARGET=$SOL_TARGET
    DEBUGGER="rust-gdb"
else
    echo "DEBUGGING THROUGH FD..."
    TARGET=$FD_TARGET
    DEBUGGER="gdb"
fi

"$DEBUGGER" --args python3.11 -m test_suite.test_suite exec-instr -t "$TARGET" -i "$1"
