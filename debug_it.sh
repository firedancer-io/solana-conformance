#!/bin/bash

# usage: ./debug_it.sh <fixture_path> [a]
# arg 1 is ctx file
# arg 2 is the target to execute, this should be a path to a .so file
# example: ./debug_it.sh <fixture_path> $FD_TARGET

source "$(dirname "$0")/test_suite_env/bin/activate"
gdb -x debug.gdb --args python3.11 -m test_suite.test_suite exec-fixtures -i "$1" -t "$2" -o scratch/debug_output --debug-mode
