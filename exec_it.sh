#!/bin/bash

# usage: ./exec_it.sh <ctx_file> [a]
# arg 1 is ctx file
# arg 2 is optional, if 'a' then use agave target, otherwise use fd target
# example: ./exec_it.sh <ctx_file> a

# make sure your python venv is activated: source solana-conformance/test_suite_env/bin/activate

if [ "$2" = "a" ]; then
    echo "EXECUTING THROUGH AGAVE..."
    TARGET=$SOL_TARGET
else
    echo "EXECUTING THROUGH FD..."
    TARGET=$FD_TARGET
fi

solana-conformance exec-instr -t "$TARGET" -i "$1"
