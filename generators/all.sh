#!/bin/bash
TESTS_PATH=./test-vectors/txn/tests/precompile
FIXTS_PATH=./test-vectors/txn/fixtures/precompile

rm -r ${TESTS_PATH}/ed25519   ; mkdir -p ${TESTS_PATH}/ed25519
python3 generators/ed25519.py
rm -r ${FIXTS_PATH}/ed25519   ; mkdir -p ${FIXTS_PATH}/ed25519
HARNESS_TYPE=TxnHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/ed25519 -o ${FIXTS_PATH}/ed25519 -s ./impl/lib/libsolfuzz_agave_v2.0.so

rm -r ${TESTS_PATH}/secp256k1 ; mkdir -p ${TESTS_PATH}/secp256k1
python3 generators/secp256k1.py
rm -r ${FIXTS_PATH}/secp256k1 ; mkdir -p ${FIXTS_PATH}/secp256k1
HARNESS_TYPE=TxnHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/secp256k1 -o ${FIXTS_PATH}/secp256k1 -s ./impl/lib/libsolfuzz_agave_v2.0.so

# TESTS_PATH=./test-vectors/syscall/tests
# FIXTS_PATH=./test-vectors/syscall/fixtures

# rm -r ${TESTS_PATH}/curve25519 ; mkdir -p ${TESTS_PATH}/curve25519
# python3 generators/syscalls_curve25519.py
# rm -r ${FIXTS_PATH}/curve25519 ; mkdir -p ${FIXTS_PATH}/curve25519
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/curve25519 -o ${FIXTS_PATH}/curve25519 -s ./impl/lib/libsolfuzz_agave_v2.0.so

# rm -r ${TESTS_PATH}/secp256k1 ; mkdir -p ${TESTS_PATH}/secp256k1
# python3 generators/syscalls_secp256k1.py
# rm -r ${FIXTS_PATH}/secp256k1 ; mkdir -p ${FIXTS_PATH}/secp256k1
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/secp256k1 -o ${FIXTS_PATH}/secp256k1 -s ./impl/lib/libsolfuzz_agave_v2.0.so

# rm -r ${TESTS_PATH}/poseidon ; mkdir -p ${TESTS_PATH}/poseidon
# python3 generators/syscalls_poseidon.py
# rm -r ${FIXTS_PATH}/poseidon ; mkdir -p ${FIXTS_PATH}/poseidon
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/poseidon -o ${FIXTS_PATH}/poseidon -s ./impl/lib/libsolfuzz_agave_v2.0.so

# rm -r ${TESTS_PATH}/alt_bn128 ; mkdir -p ${TESTS_PATH}/alt_bn128
# python3 generators/syscalls_alt_bn128.py
# rm -r ${FIXTS_PATH}/alt_bn128 ; mkdir -p ${FIXTS_PATH}/alt_bn128
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/alt_bn128 -o ${FIXTS_PATH}/alt_bn128 -s ./impl/lib/libsolfuzz_agave_v2.0.so

# rm -r ${TESTS_PATH}/sha256    ; mkdir -p ${TESTS_PATH}/sha256
# rm -r ${TESTS_PATH}/keccak256 ; mkdir -p ${TESTS_PATH}/keccak256
# rm -r ${TESTS_PATH}/blake3    ; mkdir -p ${TESTS_PATH}/blake3
# python3 generators/syscalls_hash.py
# rm -r ${FIXTS_PATH}/sha256    ; mkdir -p ${FIXTS_PATH}/sha256
# rm -r ${FIXTS_PATH}/keccak256 ; mkdir -p ${FIXTS_PATH}/keccak256
# rm -r ${FIXTS_PATH}/blake3    ; mkdir -p ${FIXTS_PATH}/blake3
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/sha256 -o ${FIXTS_PATH}/sha256 -s ./impl/lib/libsolfuzz_agave_v2.0.so
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/keccak256 -o ${FIXTS_PATH}/keccak256 -s ./impl/lib/libsolfuzz_agave_v2.0.so
# HARNESS_TYPE=SyscallHarness solana-test-suite create-fixtures -i ${TESTS_PATH}/blake3 -o ${FIXTS_PATH}/blake3 -s ./impl/lib/libsolfuzz_agave_v2.0.so
