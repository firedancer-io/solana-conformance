import hashlib
import test_suite.vm_pb2 as pbvm
from dataclasses import dataclass
import struct
from syscalls_hash import test_vectors as test_vectors_hash, heap_vec

OUTPUT_DIR = "./test-vectors/instr/inputs/20240425/syscalls/poseidon"
HEAP_START = 0x300000000
CU_BASE = 542
CU_PER_ELEM = 61
CU_MEM_OP = 10

def exact_cu_cost(data_vec):
    return CU_BASE + CU_PER_ELEM * len(data_vec) * len(data_vec)

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]

test_hello = ["hello"]
test_ones = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
test_twos = test_ones + [[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]]
test_input_one = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]]

test_with_empty = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]
test_with_non_field = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [255, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 255],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]
test_with_too_long = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]
test_with_short_ok = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
]

# all these tests either return Ok(0) or Ok(1)
test_vectors_poseidon = [
    # https://github.com/solana-labs/solana/blob/v1.18.12/sdk/program/src/poseidon.rs#L246-L247
    # this can never happen

    # https://github.com/solana-labs/solana/blob/v1.18.12/sdk/program/src/poseidon.rs#L248-L252
    {
        "heap_prefix": [0]*32 + heap_vec(test_with_empty, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_with_empty),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_with_empty)
    },
    {
        "endianness": 0,
        "heap_prefix": [0]*32 + heap_vec(test_with_non_field, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_with_non_field),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_with_non_field)
    },
    {
        "endianness": 1,
        "heap_prefix": [0]*32 + heap_vec(test_with_non_field, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_with_non_field),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_with_non_field)
    },
    {
        "heap_prefix": [0]*32 + heap_vec(test_with_too_long, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_with_too_long),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_with_too_long)
    },
    {
        "heap_prefix": [0]*32 + heap_vec(test_with_short_ok, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_with_short_ok),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_with_short_ok)
    },

    # success
    # test_poseidon_input_ones_be
    {
        "endianness": 0,
        "heap_prefix": [0]*32 + heap_vec(test_ones, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_ones),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_ones)
    },
    # test_poseidon_input_ones_le
    {
        "endianness": 1,
        "heap_prefix": [0]*32 + heap_vec(test_ones, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_ones),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_ones)
    },
    # test_poseidon_input_ones_twos_be
    {
        "endianness": 0,
        "heap_prefix": [0]*32 + heap_vec(test_twos, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_twos),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_twos)
    },
    # test_poseidon_input_ones_twos_le
    {
        "endianness": 1,
        "heap_prefix": [0]*32 + heap_vec(test_twos, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_twos),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_twos)
    },
    # test_poseidon_input_one
]
for n in range(12):
    test_input_one_times_n = test_input_one * (n+1)
    test_vectors_poseidon.append({
        "endianness": 0,
        "heap_prefix": [0]*32 + heap_vec(test_input_one_times_n, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_input_one_times_n),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_input_one_times_n)
    }),

# all these tests either return Err(.)
test_vectors_workflow = [
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1688
    {
        "params": 1,
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)
    },
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1689
    {
        "endianness": 2,
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)
    },
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1691-L1698
    {
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": 13,
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)
    },
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1701-L1707
    # this can never happen
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1708
    {
        # hash("hello") = valid
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": 1
    },
    {
        # hash("hello") = valid
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)-1
    },
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1710-L1732
    # covered by test_vectors_hash
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1738-L1747
    # FD only supports simplify_alt_bn128_syscall_error_codes
    # these are all the tests in test_vectors_poseidon
]

print("Generating syscall poseidon tests...")

test_vectors = _into_key_data("p", test_vectors_poseidon) + _into_key_data("w", test_vectors_workflow) + test_vectors_hash

for (key, test) in test_vectors:
    heap_prefix = test.get("heap_prefix", [])
    syscall_ctx = pbvm.SyscallContext()
    syscall_ctx.syscall_invocation.function_name = b"sol_poseidon"
    syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
    syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
    syscall_ctx.vm_ctx.r1 = test.get("params", 0)
    syscall_ctx.vm_ctx.r2 = test.get("endianness", 0)
    syscall_ctx.vm_ctx.r3 = test.get("vals_addr", 0)
    syscall_ctx.vm_ctx.r4 = test.get("vals_len", 0)
    syscall_ctx.vm_ctx.r5 = test.get("result_addr", 0)
    syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
    syscall_ctx.instr_ctx.program_id = bytes([0]*32) # solfuzz-agave expectes a program_id
    syscall_ctx.vm_ctx.rodata = b"x" # fd expects some bytes

    syscall_ctx.instr_ctx.epoch_context.features.features.extend([
        0x3cbf822ccb2eebd4,  # enable_poseidon_syscall
        0x8ba9e9038d9fdcff,  # simplify_alt_bn128_syscall_error_codes
    ])

    filename = str(key) + "_" + hashlib.sha3_256(syscall_ctx.instr_ctx.data).hexdigest()[:16]

    serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
    with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
        f.write(serialized_instr)

print("done!")
