#!/bin/bash
TESTS_PATH=./test-vectors/txn/tests/precompile
FIXTS_PATH=./test-vectors/txn/fixtures/precompile
LIB_SOLFUZZ_AGAVE=../solfuzz-agave/target/debug/libsolfuzz_agave.so

rm -r ${TESTS_PATH}/ed25519   ; mkdir -p ${TESTS_PATH}/ed25519
python3 generators/ed25519.py
rm -r ${FIXTS_PATH}/ed25519   ; mkdir -p ${FIXTS_PATH}/ed25519
solana-conformance create-fixtures -i ${TESTS_PATH}/ed25519 -o ${FIXTS_PATH}/ed25519 -s ${LIB_SOLFUZZ_AGAVE} -h TxnHarness

rm -r ${TESTS_PATH}/secp256k1 ; mkdir -p ${TESTS_PATH}/secp256k1
python3 generators/secp256k1.py
rm -r ${FIXTS_PATH}/secp256k1 ; mkdir -p ${FIXTS_PATH}/secp256k1
solana-conformance create-fixtures -i ${TESTS_PATH}/secp256k1 -o ${FIXTS_PATH}/secp256k1 -s ${LIB_SOLFUZZ_AGAVE} -h TxnHarness

rm -r ${TESTS_PATH}/secp256r1 ; mkdir -p ${TESTS_PATH}/secp256r1
python3 generators/precompile_secp256r1.py
rm -r ${FIXTS_PATH}/secp256r1 ; mkdir -p ${FIXTS_PATH}/secp256r1
solana-conformance create-fixtures -i ${TESTS_PATH}/secp256r1 -o ${FIXTS_PATH}/secp256r1 -s ${LIB_SOLFUZZ_AGAVE} -h TxnHarness

TESTS_PATH=./test-vectors/syscall/tests
FIXTS_PATH=./test-vectors/syscall/fixtures

rm -r ${TESTS_PATH}/curve25519 ; mkdir -p ${TESTS_PATH}/curve25519
python3 generators/syscalls_curve25519.py
rm -r ${FIXTS_PATH}/curve25519 ; mkdir -p ${FIXTS_PATH}/curve25519
solana-conformance create-fixtures -i ${TESTS_PATH}/curve25519 -o ${FIXTS_PATH}/curve25519 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness

rm -r ${TESTS_PATH}/secp256k1 ; mkdir -p ${TESTS_PATH}/secp256k1
python3 generators/syscalls_secp256k1.py
rm -r ${FIXTS_PATH}/secp256k1 ; mkdir -p ${FIXTS_PATH}/secp256k1
solana-conformance create-fixtures -i ${TESTS_PATH}/secp256k1 -o ${FIXTS_PATH}/secp256k1 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness

rm -r ${TESTS_PATH}/poseidon ; mkdir -p ${TESTS_PATH}/poseidon
python3 generators/syscalls_poseidon.py
rm -r ${FIXTS_PATH}/poseidon ; mkdir -p ${FIXTS_PATH}/poseidon
solana-conformance create-fixtures -i ${TESTS_PATH}/poseidon -o ${FIXTS_PATH}/poseidon -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness

rm -r ${TESTS_PATH}/alt_bn128 ; mkdir -p ${TESTS_PATH}/alt_bn128
python3 generators/syscalls_alt_bn128.py
rm -r ${FIXTS_PATH}/alt_bn128 ; mkdir -p ${FIXTS_PATH}/alt_bn128
solana-conformance create-fixtures -i ${TESTS_PATH}/alt_bn128 -o ${FIXTS_PATH}/alt_bn128 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness

rm -r ${TESTS_PATH}/sha256    ; mkdir -p ${TESTS_PATH}/sha256
rm -r ${TESTS_PATH}/keccak256 ; mkdir -p ${TESTS_PATH}/keccak256
rm -r ${TESTS_PATH}/blake3    ; mkdir -p ${TESTS_PATH}/blake3
python3 generators/syscalls_hash.py
rm -r ${FIXTS_PATH}/sha256    ; mkdir -p ${FIXTS_PATH}/sha256
rm -r ${FIXTS_PATH}/keccak256 ; mkdir -p ${FIXTS_PATH}/keccak256
rm -r ${FIXTS_PATH}/blake3    ; mkdir -p ${FIXTS_PATH}/blake3
solana-conformance create-fixtures -i ${TESTS_PATH}/sha256 -o ${FIXTS_PATH}/sha256 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
solana-conformance create-fixtures -i ${TESTS_PATH}/keccak256 -o ${FIXTS_PATH}/keccak256 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
solana-conformance create-fixtures -i ${TESTS_PATH}/blake3 -o ${FIXTS_PATH}/blake3 -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness

rm -r ${TESTS_PATH}/panic ; mkdir -p ${TESTS_PATH}/panic
rm -r ${TESTS_PATH}/abort ; mkdir -p ${TESTS_PATH}/abort
rm -r ${TESTS_PATH}/log ; mkdir -p ${TESTS_PATH}/log
rm -r ${TESTS_PATH}/log_data ; mkdir -p ${TESTS_PATH}/log_data
python3 generators/syscalls_util.py
rm -r ${FIXTS_PATH}/panic ; mkdir -p ${FIXTS_PATH}/panic
rm -r ${FIXTS_PATH}/abort ; mkdir -p ${FIXTS_PATH}/abort
rm -r ${FIXTS_PATH}/log ; mkdir -p ${FIXTS_PATH}/log
rm -r ${FIXTS_PATH}/log_data ; mkdir -p ${FIXTS_PATH}/log_data
solana-conformance create-fixtures -i ${TESTS_PATH}/panic -o ${FIXTS_PATH}/panic -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
solana-conformance create-fixtures -i ${TESTS_PATH}/abort -o ${FIXTS_PATH}/abort -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
solana-conformance create-fixtures -i ${TESTS_PATH}/log -o ${FIXTS_PATH}/log -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
solana-conformance create-fixtures -i ${TESTS_PATH}/log_data -o ${FIXTS_PATH}/log_data -s ${LIB_SOLFUZZ_AGAVE} -h SyscallHarness
