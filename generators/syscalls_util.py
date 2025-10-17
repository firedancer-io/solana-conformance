import hashlib
import test_suite.protos.vm_pb2 as vm_pb
import struct

OUTPUT_DIR = "./test-vectors/syscall/tests/"
HEAP_START = 0x300000000
STACK_START = 0x200000000

CU_BASE_LOG = 100
CU_PER_BYTE = 1  # this is actually every 2 bytes...
CU_MEM_OP = 10


def heap_vec(data_vec, start):
    res = []
    last = start + len(data_vec) * 16
    for data in data_vec:
        res += struct.pack("<Q", last)
        res += struct.pack("<Q", len(data))
        last += len(data)
    for data in data_vec:
        if isinstance(data, str):
            res += bytes(data, "ascii")
        else:
            res += bytes(data)
    return res


msg_hello = bytes("hello", "ascii")
msg_utf8 = bytes("grüezi\0\n🔥💃", "utf8")
msg_invalid_utf8 = bytes([0xE0, 0x80, 0x80])


def exact_cu_cost(data_vec):
    return 100 + 100 * len(data_vec) + sum([len(x) for x in data_vec])


test_vectors_abort = [
    {
        "cu_avail": 1,
    },
    {
        "cu_avail": 0,
    },
    {
        "r1": 5,  # useless
        "cu_avail": 0,
    },
]

panic_msg = msg_hello
panic_utf8 = msg_utf8
panic_invalid = msg_invalid_utf8
panic_msg_max = bytes(
    "x"
    * (
        10000
        - len(
            "Program 11111111111111111111111111111111 failed: SBF program Panicked in | at 10:100"
        )
    ),
    "ascii",
)
panic_msg_20k = bytes("y" * 20 * 1024, "ascii")
test_vectors_panic = [
    {
        # ok... well, panic :)
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": len(panic_msg),
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_msg),
    },
    {
        "heap_prefix": panic_utf8,
        "file": HEAP_START,
        "file_sz": len(panic_utf8),
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_utf8),
    },
    {
        "heap_prefix": panic_invalid,
        "file": HEAP_START,
        "file_sz": len(panic_invalid),
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_invalid),
    },
    {
        # CU
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": len(panic_msg),
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_msg) - 1,
    },
    {
        # file_sz = 0
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": 0,
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_msg),
    },
    {
        # file_sz = 0 and cu = 0
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": 0,
        "line": 1,
        "column": 2,
        "cu_avail": 0,
    },
    {
        # file_sz > heap_sz
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": len(panic_msg) + 1,
        "line": 1,
        "column": 2,
        "cu_avail": len(panic_msg),
    },
    {
        # large line, column - ok
        "heap_prefix": panic_msg,
        "file": HEAP_START,
        "file_sz": len(panic_msg),
        "line": 0xFFFFFFFFFFFFFFFF,
        "column": 0xFFFFFFFFFFFFFFFF,
        "cu_avail": len(panic_msg),
    },
    {
        # very large file_sz
        "heap_prefix": panic_msg_20k,
        "file": HEAP_START,
        "file_sz": len(panic_msg_20k),
        "line": 0xFFFFFFFFFFFFFFFF,
        "column": 0xFFFFFFFFFFFFFFFF,
        "cu_avail": len(panic_msg_20k),
    },
    {
        # max file_sz + 1
        "heap_prefix": panic_msg_20k,
        "file": HEAP_START,
        "file_sz": len(panic_msg_max) + 1,
        "line": 10,
        "column": 100,
        "cu_avail": len(panic_msg_20k),
    },
    {
        # max file_sz
        "heap_prefix": panic_msg_max,
        "file": HEAP_START,
        "file_sz": len(panic_msg_max),
        "line": 10,
        "column": 100,
        "cu_avail": len(panic_msg_max),
    },
]

logs = [
    msg_hello,
    msg_utf8,
    msg_invalid_utf8,
    bytes([]),
    bytes("a" * 99, "ascii"),
    bytes("b" * 100, "ascii"),  # cus switch from base to msg_sz
    bytes("c" * 101, "ascii"),
    bytes("x" * (10_000 - len("Program log: ") - 1), "ascii"),
    bytes("y" * (10_000 - len("Program log: ")), "ascii"),
    bytes("z" * 30_000, "ascii"),
]
test_vectors_log = []
for log in logs:
    test_vectors_log += [
        {
            "heap_prefix": log,
            "msg": HEAP_START,
            "msg_sz": len(log),
            "cu_avail": max(CU_BASE_LOG, len(log)),
        },
        {
            "heap_prefix": log,
            "msg": HEAP_START,
            "msg_sz": len(log),
            "cu_avail": max(CU_BASE_LOG, len(log)) - 1,
        },
    ]

test_vectors_log64 = [
    {
        # ok
        "r1": 0,
        "r2": 0,
        "r3": 0,
        "r4": 0,
        "r5": 0,
        "cu_avail": 100,
    },
    {
        # ok
        "r1": 0xFFFFFFFFFFFFFFFF,
        "r2": 0xFFFFFFFFFFFFFFFF,
        "r3": 0xFFFFFFFFFFFFFFFF,
        "r4": 0xFFFFFFFFFFFFFFFF,
        "r5": 0xFFFFFFFFFFFFFFFF,
        "cu_avail": 100,
    },
    {
        # cu
        "r1": 0,
        "r2": 0,
        "r3": 0,
        "r4": 0,
        "r5": 0,
        "cu_avail": 99,
    },
]

test_vectors_log_cu = [
    {
        "cu_avail": 100,
    },
    {
        "cu_avail": 99,
    },
    {
        "cu_avail": 101,
    },
    {
        "cu_avail": 0xFFFFFFFFFFFFFFFF,
    },
]

test_vectors_log_pk = [
    {
        "heap_prefix": bytes([0] * 32),
        "pubkey_vaddr": HEAP_START,
        "cu_avail": 100,
    },
    {
        "heap_prefix": bytes([0] * 31),
        "pubkey_vaddr": HEAP_START,
        "cu_avail": 100,
    },
    {
        "heap_prefix": bytes([0] * 32),
        "pubkey_vaddr": HEAP_START + 1,
        "cu_avail": 100,
    },
    {
        "heap_prefix": bytes([0] * 32),
        "pubkey_vaddr": HEAP_START,
        "cu_avail": 99,
    },
]

test_hello = [msg_hello]
test_hello_world = [msg_hello, "world"]
test_many = [msg_hello, msg_utf8, msg_invalid_utf8, "world"]
test_truncate_1 = [bytes([1] * (7489))]
test_truncate_1_dont = [bytes([1] * (7489 - 1))]
test_truncate_2 = [msg_hello, bytes([2] * (7483))]
test_truncate_2_dont = [msg_hello, bytes([2] * (7483 - 1))]
test_big = [msg_hello] * 1000

# large array of refs all to invalid mem
# neither fd nor agave should attempt to read
msg_stack = []
msg_stack += struct.pack("<Q", STACK_START - 1)  # invalid ref
msg_stack += struct.pack("<Q", 4096 * 2)  # invalid length
test_massive = [msg_stack] * 1024  # must fit in the heap

# access violation on 2nd element
test_many_faulty = heap_vec(test_many, HEAP_START)
test_many_faulty[20] = 0

test_vectors_log_data = [
    {
        # valid
        "heap_prefix": bytes([]),
        "slice_vaddr": HEAP_START,
        "slice_cnt": 0,
        "cu_avail": 100,
    },
    {
        # valid
        "heap_prefix": heap_vec(test_hello, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_hello),
        "cu_avail": exact_cu_cost(test_hello),
    },
    {
        # valid
        "heap_prefix": heap_vec(test_hello_world, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_hello_world),
        "cu_avail": exact_cu_cost(test_hello_world),
    },
    {
        # valid
        "heap_prefix": heap_vec(test_many, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_many),
        "cu_avail": exact_cu_cost(test_many),
    },
    {
        # cu
        "heap_prefix": bytes([]),
        "slice_vaddr": HEAP_START,
        "slice_cnt": 0,
        "cu_avail": 99,
    },
    {
        # cu
        "heap_prefix": heap_vec(test_hello_world, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_hello_world),
        "cu_avail": exact_cu_cost(test_hello_world) - 1,
    },
    {
        # truncate
        "heap_prefix": heap_vec(test_truncate_1, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_truncate_1),
        "cu_avail": exact_cu_cost(test_truncate_1),
    },
    {
        # truncate (1 less byte)
        "heap_prefix": heap_vec(test_truncate_1_dont, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_truncate_1_dont),
        "cu_avail": exact_cu_cost(test_truncate_1_dont),
    },
    {
        # truncate 2
        "heap_prefix": heap_vec(test_truncate_2, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_truncate_2),
        "cu_avail": exact_cu_cost(test_truncate_2),
    },
    {
        # truncate 2 (1 less byte)
        "heap_prefix": heap_vec(test_truncate_2_dont, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_truncate_2_dont),
        "cu_avail": exact_cu_cost(test_truncate_2_dont),
    },
    {
        # valid
        "heap_prefix": heap_vec(test_big, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_big),
        "cu_avail": exact_cu_cost(test_big),
    },
    {
        # truncated
        "heap_prefix": heap_vec(test_massive, HEAP_START),
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_massive),
        "cu_avail": exact_cu_cost(test_massive),
    },
    {
        # invalid mem
        "heap_prefix": test_many_faulty,
        "slice_vaddr": HEAP_START,
        "slice_cnt": len(test_many),
        "cu_avail": exact_cu_cost(test_many),
    },
]


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


test_vectors_abort = _into_key_data("a", test_vectors_abort)
test_vectors_panic = _into_key_data("p", test_vectors_panic)
test_vectors_log = _into_key_data("log", test_vectors_log)
test_vectors_log64 = _into_key_data("log_64", test_vectors_log64)
test_vectors_log_cu = _into_key_data("log_cu", test_vectors_log_cu)
test_vectors_log_pk = _into_key_data("log_pk", test_vectors_log_pk)
test_vectors_log_data = _into_key_data("ld", test_vectors_log_data)

if __name__ == "__main__":
    print("Generating syscalls abort...")

    for key, test in test_vectors_abort:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("abort", "ascii")
        syscall_ctx.vm_ctx.r1 = test.get("r1", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/abort/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("Generating syscalls panic...")

    for key, test in test_vectors_panic:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("sol_panic_", "ascii")
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("file", 0)
        syscall_ctx.vm_ctx.r2 = test.get("file_sz", 0)
        syscall_ctx.vm_ctx.r3 = test.get("line", 0)
        syscall_ctx.vm_ctx.r4 = test.get("column", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/panic/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("Generating syscalls log...")

    for key, test in test_vectors_log:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("sol_log_", "ascii")
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("msg", 0)
        syscall_ctx.vm_ctx.r2 = test.get("msg_sz", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/log/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("Generating syscalls log_64...")

    for key, test in test_vectors_log64:
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("sol_log_64_", "ascii")
        syscall_ctx.vm_ctx.r1 = test.get("r1", 0)
        syscall_ctx.vm_ctx.r2 = test.get("r2", 0)
        syscall_ctx.vm_ctx.r3 = test.get("r3", 0)
        syscall_ctx.vm_ctx.r4 = test.get("r4", 0)
        syscall_ctx.vm_ctx.r5 = test.get("r5", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/log/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("Generating syscalls log_compute_units...")

    for key, test in test_vectors_log_cu:
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes(
            "sol_log_compute_units_", "ascii"
        )
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.vm_ctx.r1 = 0  # solfuzz-agave expectes at least a register
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/log/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("Generating syscalls log_pubkey...")

    for key, test in test_vectors_log_pk:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("sol_log_pubkey", "ascii")
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("pubkey_vaddr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/log/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    for key, test in test_vectors_log_data:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = bytes("sol_log_data", "ascii")
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("slice_vaddr", 0)
        syscall_ctx.vm_ctx.r2 = test.get("slice_cnt", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/log_data/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
