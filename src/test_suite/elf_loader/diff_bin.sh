#!/usr/bin/bash

# This script diff's two hexdump'd files
# Usage: diff.sh file1 file2

# Check if the number of arguments is correct
if [ $# -lt 2 ]; then
    echo "Usage: $0 file1 file2"
    exit 1
fi

# Check if the files exist

if [ ! -f $1 ]; then
    echo "File $1 does not exist"
    exit 1
fi

if [ ! -f $2 ]; then
    echo "File $2 does not exist"
    exit 1
fi

file1=$1
file2=$2
shift 2

diff <(xxd $file1) <(xxd $file2) $@