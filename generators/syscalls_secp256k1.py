import hashlib
import test_suite.invoke_pb2 as pb
from eth_hash.auto import keccak

OUTPUT_DIR = "./test-vectors/instr/inputs/20240425/syscalls/secp256k1"
HEAP_START = 0x300000000
CU_BASE = 25_000

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]

pubkey = [129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101]
sig =         [14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3]
sig_invalid = [255]*64
sig_err     = [14, 196, 198, 193, 237, 0, 14, 255, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3]
#                                             ^^^ modified byte
recid = 1
msg = [104, 101, 108, 108, 111]  # hello
hash = list(keccak(bytes(msg)))

# all these tests either return Err(.)
test_vectors_workflow = [
    # valid
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": sig + hash,
        "hash_vaddr": HEAP_START + 64,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": hash + sig,
        "hash_vaddr": HEAP_START,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 32,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L820-L821
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE - 1
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L823-L828
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 129,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START - 1,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": 0x500000000,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L829-L834
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 128,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START -1,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": 0,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L835-L840
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START + 128,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START - 1,
        "cu_avail": CU_BASE
    },
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": 0,
        "cu_avail": CU_BASE
    },

    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L842-L844
    # this can never happen

    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L845-L847
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": 1000,  # not a u8
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },

    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L848-L850
    {
        "heap_prefix": [0]*64 + sig + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": 4,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },

    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L851-L853
    {
        "heap_prefix": [0]*64 + sig_invalid + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },

    # https://github.com/anza-xyz/agave/blob/v1.18.8/programs/bpf_loader/src/syscalls/mod.rs#L858
    {
        "heap_prefix": [0]*64 + sig_err + hash,
        "hash_vaddr": HEAP_START + 128,
        "recovery_id_val": recid,
        "signature_vaddr": HEAP_START + 64,
        "result_vaddr": HEAP_START,
        "cu_avail": CU_BASE
    },
]

test_vectors = _into_key_data("w", test_vectors_workflow)

if __name__ == "__main__":
    print("Generating syscall secp256k1 tests...")

    for (key, test) in test_vectors:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_secp256k1_recover"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("hash_vaddr", 0)
        syscall_ctx.vm_ctx.r2 = test.get("recovery_id_val", 0)
        syscall_ctx.vm_ctx.r3 = test.get("signature_vaddr", 0)
        syscall_ctx.vm_ctx.r4 = test.get("result_vaddr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes([0]*32) # solfuzz-agave expectes a program_id
        syscall_ctx.vm_ctx.rodata = b"x" # fd expects some bytes

        syscall_ctx.instr_ctx.epoch_context.features.features.extend([
            0x4ab8b2b10003ad50,  # secp256k1_recover_syscall_enabled
        ])

        filename = str(key) + "_" + hashlib.sha3_256(syscall_ctx.instr_ctx.data).hexdigest()[:16]

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
