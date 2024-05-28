#!/bin/bash
TESTS_PATH=./test-vectors/instr/inputs/20240425
rm ${TESTS_PATH}/ed25519/* ;            python3 generators/ed25519.py
rm ${TESTS_PATH}/secp256k1/* ;          python3 generators/secp256k1.py
rm ${TESTS_PATH}/syscalls/keccak256/*
rm ${TESTS_PATH}/syscalls/blake3/*
rm ${TESTS_PATH}/syscalls/sha256/* ;    python3 generators/syscalls_hash.py
rm ${TESTS_PATH}/syscalls/secp256k1/* ; python3 generators/syscalls_secp256k1.py
rm ${TESTS_PATH}/syscalls/poseidon/* ;  python3 generators/syscalls_poseidon.py
rm ${TESTS_PATH}/syscalls/alt_bn128/* ; python3 generators/syscalls_alt_bn128.py
