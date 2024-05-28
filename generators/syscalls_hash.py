import hashlib
import test_suite.invoke_pb2 as pb
import struct

OUTPUT_DIR = "./test-vectors/instr/inputs/20240425/syscalls"
HEAP_START = 0x300000000
CU_BASE = 85
CU_PER_BYTE = 1  # this is actually every 2 bytes...
CU_MEM_OP = 10

def heap_vec(data_vec, start):
    res = []
    last = start + len(data_vec) * 16
    for data in data_vec:
        res += struct.pack('<Q', last)
        res += struct.pack('<Q', len(data))
        last += len(data)
    for data in data_vec:
        if isinstance(data, str):
            res += bytes(data, "ascii")
        else:
            res += bytes(data)
    return res

def exact_cu_cost(data_vec):
    return CU_BASE + sum([max((len(x) / 2)*CU_PER_BYTE, CU_MEM_OP) for x in data_vec])

# https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L2521
test_hello = ["hello"]
test_hello_world = ["hello", " world"]
test_vectors_hash = [
    {
        # empty hash = valid
        "heap_prefix": [0]*32,
        "result_addr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        # hash("hello") = valid
        "heap_prefix": [0]*32 + heap_vec(test_hello, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)
    },
    {
        # hash("hello") = valid
        # result at the end
        "heap_prefix": heap_vec(test_hello, HEAP_START + 32) + [0]*32,
        "vals_addr": HEAP_START,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START + len(heap_vec(test_hello, HEAP_START + 32)),
        "cu_avail": exact_cu_cost(test_hello)
    },
    {
        # hash("hello") = valid
        # result overwrites input
        "heap_prefix": heap_vec(test_hello, HEAP_START) + [0]*11,
        "vals_addr": HEAP_START,
        "vals_len": len(test_hello),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello)
    },
    {
        # hash("hello world") = valid
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    # SyscallError::TooManySlices
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1919
    {
        # fail max slices
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": 20001,
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    # ComputationalBudgetExceeded
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1922
    {
        # fail cu begin
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": 1
    },

    # translate_slice_mut
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1924-L1929
    # TODO: cover all errors, e.g. UnalignedPointer
    {
        # fail alloc result
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START - 1,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    {
        # fail alloc result
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START - 64,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    {
        # fail alloc result (2)
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START + 100,
        "cu_avail": exact_cu_cost(test_hello_world)
    },

    # translate_slice
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1932-L1937
    # TODO: cover all errors, e.g. UnalignedPointer
    {
        # fail alloc vec
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START - 1,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    {
        # fail alloc vec (2)
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 100,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1939-L1944
    {
        # fail alloc elem
        "heap_prefix": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 164, 0, 0, 0, 3, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 69, 0, 0, 0, 3, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100],
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },
    {
        # fail alloc elem
        "heap_prefix": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 3, 0, 0, 0, 105, 0, 0, 0, 0, 0, 0, 0, 69, 0, 0, 0, 3, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 104, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100],
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": exact_cu_cost(test_hello_world)
    },

    # ComputationalBudgetExceeded
    # https://github.com/solana-labs/solana/blob/v1.18.12/programs/bpf_loader/src/syscalls/mod.rs#L1945-L1952
    {
        # fail cu middle
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        # fail cu end
        "heap_prefix": [0]*32 + heap_vec(test_hello_world, HEAP_START + 32),
        "vals_addr": HEAP_START + 32,
        "vals_len": len(test_hello_world),
        "result_addr": HEAP_START,
        "cu_avail": CU_BASE + 12
    },
]

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]

test_vectors = _into_key_data("h", test_vectors_hash)

if __name__ == "__main__":
    print("Generating syscalls sha256, keccak256, blake3 tests...")

    for (key, test) in test_vectors:
        for hash in ["sha256", "keccak256", "blake3"]:
            heap_prefix = test.get("heap_prefix", [])
            syscall_ctx = pb.SyscallContext()
            syscall_ctx.syscall_invocation.function_name = bytes("sol_" + hash, "ascii")
            syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
            syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
            syscall_ctx.vm_ctx.r1 = test.get("vals_addr", 0)
            syscall_ctx.vm_ctx.r2 = test.get("vals_len", 0)
            syscall_ctx.vm_ctx.r3 = test.get("result_addr", 0)
            syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
            syscall_ctx.instr_ctx.program_id = bytes([0]*32) # solfuzz-agave expectes a program_id
            syscall_ctx.vm_ctx.rodata = b"x" # fd expects some bytes

            syscall_ctx.instr_ctx.epoch_context.features.features.extend([0xe994a4b8eeea84f4]) # enable blake3

            filename = str(key) + "_" + hashlib.sha3_256(syscall_ctx.instr_ctx.data).hexdigest()[:16]

            serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
            with open(f"{OUTPUT_DIR}/{hash}/{filename}.bin", "wb") as f:
                f.write(serialized_instr)

    print("done!")
