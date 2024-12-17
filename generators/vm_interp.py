import hashlib
import test_suite.vm_pb2 as vm_pb
import struct

OUTPUT_DIR = "./test-vectors/vm_interp/tests/"
HEAP_START = 0x300000000
STACK_START = 0x200000000

CU_BASE_LOG = 100
CU_PER_BYTE = 1  # this is actually every 2 bytes...
CU_MEM_OP = 10

# fmt: off
INVALID_IXS = [
    0x00, 0x01, 0x02, 0x03, 0x06, 0x08, 0x09, 0x0a, 0x0b, 0x0d, 0x0e, 
    0x10, 0x11, 0x12, 0x13, 0x16, 0x18, 0x19, 0x1a, 0x1b,       0x1e,
    0x20, 0x21, 0x22, 0x23, 0x26, 0x28, 0x29, 0x2a, 0x2b,       0x2e,
    0x30, 0x31, 0x32, 0x33,       0x38, 0x39, 0x3a, 0x3b,
    0x40, 0x41, 0x42, 0x43,       0x48, 0x49, 0x4a, 0x4b,
    0x50, 0x51, 0x52, 0x53,       0x58, 0x59, 0x5a, 0x5b,
    0x60, 0x68,
    0x70, 0x78,
    0x80, 0x81, 0x82, 0x83,       0x88, 0x89, 0x8a, 0x8b,
    0x90, 0x91, 0x92, 0x93,       0x98, 0x99, 0x9a, 0x9b,
    0xa0, 0xa1, 0xa2, 0xa3, 0xa6, 0xa8, 0xa9, 0xaa, 0xab,       0xae,
    0xb0, 0xb1, 0xb2, 0xb3,       0xb8, 0xb9, 0xba, 0xbb,
    0xc0, 0xc1, 0xc2, 0xc3,       0xc8, 0xc9, 0xca, 0xcb,
    0xd0, 0xd1, 0xd2, 0xd3, 0xd7, 0xd8, 0xd9, 0xda, 0xdb,       0xdf,
    0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe7, 0xe8, 0xe9, 0xea, 0xeb, 0xec, 0xed, 0xef,
    0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xff, 
]

LOAD_STORE_IXS = [
    # v0
    0x61, 0x62, 0x63, 0x69, 0x6a, 0x6b,
    0x71, 0x72, 0x73, 0x79, 0x7a, 0x7b,
    # v2
    # 0x27, 0x2c, 0x2f,
    # 0x37, 0x3c, 0x3f,
    # 0x87, 0x8c, 0x8f,
    # 0x97, 0x9c, 0x9f,
]
# fmt: on


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


def exact_cu_cost(data_vec):
    return 100 + 100 * len(data_vec) + sum([len(x) for x in data_vec])


# fmt: off
test_vectors_all_ix = []
for op in range(0xFF):
# for op in [0x07]:
    def validate():
        for sreg in [0, 2, 6, 9, 10, 11]:
            for dreg in [0, 9, 10, 11]:
                for imm in [0x0, 0x2, 0xA, 0x10, 0x20, 0x39, 0x40, 0x41, 0x12345678, 0x7fffffff, 0x80000000, 0xffffffff]:
                    test_vectors_all_ix.append({
                        "op": f"{op:02x}",
                        "cu_avail": 100,
                        "r2": 0xffffffff,
                        "r6": 0xffffffffffff,
                        "r9": 0xffffffffffffffff,
                        "rodata":
                            bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                            bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                    })
                    # for ix that we know are invalid, we only emit 1 test case
                    if op in INVALID_IXS:
                        return

    # generate most tests
    validate()

    # generate programs with length that's not a multiple of 8
    if op == 0x00:
        for i in range(8):
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                "rodata":
                    bytes([0x95] + [0]*i)
            })
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                "rodata":
                    bytes([0x95] + [0]*i) + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
            })

    # 0x18 = lddw (v0, v1) - ix 0x18 followed by 0x00
    if op == 0x18:
        sreg = 0
        dreg = 0
        imm = 0x12345678
        test_vectors_all_ix.append({
            "op": f"{op:02x}",
            "cu_avail": 100,
            "r2": 0xffffffff,
            "r6": 0xffffffffffff,
            "r9": 0xffffffffffffffff,
            "rodata":
                bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little")
        })

        for sreg in [2, 10]:
            for dreg in [0, 9, 10]:
                for imm2 in [0x0, 0x7fffffff, 0x80000001, 0xfffffffe]:
                    for imm in [0x0, 0x2, 0x12345678, 0x7fffffff, 0x80000000, 0xffffffff]:
                        test_vectors_all_ix.append({
                            "op": f"{op:02x}",
                            "cu_avail": 100,
                            "r2": 0xffffffff,
                            "r6": 0xffffffffffff,
                            "r9": 0xffffffffffffffff,
                            "rodata":
                                bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                                bytes([0x00, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm2.to_bytes(4, "little") + \
                                bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                        })
                        test_vectors_all_ix.append({
                            "op": f"{op:02x}",
                            "cu_avail": 100,
                            "r2": 0xffffffff,
                            "r6": 0xffffffffffff,
                            "r9": 0xffffffffffffffff,
                            "rodata":
                                bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                                bytes([0x00, (((sreg + 1) << 4) + dreg) % 0xFF, 0, 0]) + imm2.to_bytes(4, "little") + \
                                bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                        })
                        test_vectors_all_ix.append({
                            "op": f"{op:02x}",
                            "cu_avail": 100,
                            "r2": 0xffffffff,
                            "r6": 0xffffffffffff,
                            "r9": 0xffffffffffffffff,
                            "rodata":
                                bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                                bytes([0x00, ((sreg << 4) + (dreg - 1)) % 0xFF, 0, 0]) + imm2.to_bytes(4, "little") + \
                                bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                        })

    # call
    if op == 0x85:
        sreg = 0
        dreg = 0
        for imm in [
            0x53075d44, # pchash(1) - success
            0x63852afc, # pchash(0) - SIGSTACK
            0xc61fa2f4, # pchash(2) - fail
            0xa33b57b3, # pchash(3) - illegal ix (not in call_whitelist)
            0xd0220d26, # pchash(4) - illegal ix (not in call_whitelist)
            0x71e3cf81, # magic - always SIGSTACK (ignore call_whitelist)
            0x12345678, # invalid
            0x0b00c380, # inverse of magic - just invalid
            0x3770fb22, # syscall: sol_memset_
            1,          # success without relocation. works in v3+
            0,
            2,
            3,
            4,
            0xffffffff, # overflow ok because of negative offsets
        ]:
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                # hashmap containing valid function
                "call_whitelist": [0x04],
                "rodata":
                    bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0]) + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
            })
            # TODO: the following generates invalid functions to test validate()
            #       it's ok in v0-v2, it should return -2 in v3+
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                # hashmap containing valid pc: 0, 1, 2 (higher are trimmed)
                # these are invalid fn in v3+
                "call_whitelist": [0xff],
                "rodata":
                    bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0]) + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
            })
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                # no hashmap
                # "call_whitelist": [0x00],
                "rodata":
                    bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0]) + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
            })

    # callx
    if op == 0x8d:
        sreg = 3
        dreg = 0
        imm = 3
        for r3 in [
            0x100000000, # SIGSTACK
            0x100000008, # working
            0x100000010, # target_pc=2 > 1
            0x200000008, # region=2 != 1
            0x100000009, # !aligned
            0x200000009, # region=2 != 1 && !aligned
            0x100000011, # target_pc=2 > 1 && !aligned
            0x200000010, # target_pc=2 > 1 && region=2 != 1
            0x200000011, # target_pc=2 > 1 && region=2 != 1 && !aligned
            0xfffffffffffffff8, # overflow
        ]:
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                "r3": r3,
                "rodata":
                    bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + imm.to_bytes(4, "little") + \
                    bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
            })

    # load/store ops
    if op in LOAD_STORE_IXS:
        for reg in [
            0x0FFFFFFFF,
            0x100000000,
            0x1FFFFFFFF,
            0x200000000,
            0x200000008,
            0x2FFFFFFFF,
            0x300000000,
            0x3FFFFFFFF,
            0x400000000,
            0x4FFFFFFFF,
            0xffffffffffffffff,
        ]:
            for offset in [0x0000, 0x0001, 0x0008, 0x00FF, 0x01FF, 0xFFF8, 0xFFFF]:
                sreg = 2
                dreg = 3
                imm = reg & 0xffffffff
                test_vectors_all_ix.append({
                    "op": f"{op:02x}",
                    "cu_avail": 100,
                    "r2": reg,
                    "r3": reg,
                    "stack_prefix": [1, 2, 3, 4, 5, 6, 7, 8]*4,
                    "heap_prefix": [1, 2, 3, 4, 5, 6, 7, 8]*4,
                    "input_data_region": [1, 2, 3, 4, 5, 6, 7, 8]*4,
                    "rodata":
                        bytes([op, ((sreg << 4) + dreg) % 0xFF]) + offset.to_bytes(2, "little") + imm.to_bytes(4, "little") + \
                        bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                })

    if op in [0xc6, 0xce, 0xd6, 0xde, 0xe6, 0xee, 0xf6, 0xfe]:
        sreg = 2
        dreg = 3
        for imm in [0x0, 0xffffffffffffffff]:
            for r3 in [
                0x80000000,         # not INT_MIN / LONG_MIN
                0xffffffff80000000, # INT_MIN
                0x8000000000000000, # LONG_MIN
            ]:
                test_vectors_all_ix.append({
                    "op": f"{op:02x}",
                    "cu_avail": 100,
                    "r2": imm,
                    "r3": r3,
                    "rodata":
                        bytes([op, ((sreg << 4) + dreg) % 0xFF, 0, 0]) + (imm & 0xFFFFFFFF).to_bytes(4, "little") + \
                        bytes([0x95, 0, 0, 0, 0, 0, 0, 0])
                })

    # syscall (v3)
    if op == 0x95:
        sreg = 0
        dreg = 0
        for imm in [
            3,   # sol_memset_
            100, # invalid
        ]:
            test_vectors_all_ix.append({
                "op": f"{op:02x}",
                "cu_avail": 100,
                "rodata":
                    bytes([  op, 0, 0, 0]) + imm.to_bytes(4, "little") + \
                    bytes([0x9d, 0, 0, 0, 0, 0, 0, 0])
            })
# fmt: on


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


test_vectors_all_ix = _into_key_data("v", test_vectors_all_ix)

if __name__ == "__main__":
    print("Generating tests for all SBF instructions...")

    for key, test in test_vectors_all_ix:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = vm_pb.SyscallContext()

        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.vm_ctx.r0 = test.get("r0", 0)
        # syscall_ctx.vm_ctx.r1 = test.get("r1", 0)
        syscall_ctx.vm_ctx.r2 = test.get("r2", 0)
        syscall_ctx.vm_ctx.r3 = test.get("r3", 0)
        syscall_ctx.vm_ctx.r4 = test.get("r4", 0)
        syscall_ctx.vm_ctx.r5 = test.get("r5", 0)
        syscall_ctx.vm_ctx.r6 = test.get("r6", 0)
        syscall_ctx.vm_ctx.r7 = test.get("r7", 0)
        syscall_ctx.vm_ctx.r8 = test.get("r8", 0)
        syscall_ctx.vm_ctx.r9 = test.get("r9", 0)
        # syscall_ctx.vm_ctx.r10 = test.get("r10", 0)
        # syscall_ctx.vm_ctx.r11 = test.get("r11", 0)
        syscall_ctx.vm_ctx.rodata = test.get("rodata")
        syscall_ctx.vm_ctx.call_whitelist = bytes(
            [b for x in test.get("call_whitelist", []) for b in x.to_bytes(8, "little")]
        )
        syscall_ctx.syscall_invocation.heap_prefix = bytes(test.get("heap_prefix", []))
        syscall_ctx.vm_ctx.heap_max = len(syscall_ctx.syscall_invocation.heap_prefix)
        syscall_ctx.syscall_invocation.stack_prefix = bytes(
            test.get("stack_prefix", [])
        )
        input_data_region = bytes(test.get("input_data_region", []))
        if input_data_region:
            region = vm_pb.InputDataRegion()
            region.offset = 0
            region.content = input_data_region
            region.is_writable = True
            syscall_ctx.vm_ctx.input_data_regions.append(region)

        testname = "validate"
        syscall_ctx.vm_ctx.sbpf_version = 0
        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = (
            "ix_"
            + test.get("op")
            + "_"
            + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        )
        with open(f"{OUTPUT_DIR}/{testname}/v0/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

        syscall_ctx.vm_ctx.sbpf_version = 1
        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        with open(f"{OUTPUT_DIR}/{testname}/v1/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

        syscall_ctx.vm_ctx.sbpf_version = 2
        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        with open(f"{OUTPUT_DIR}/{testname}/v2/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

        syscall_ctx.vm_ctx.sbpf_version = 3
        syscall_ctx.vm_ctx.rodata = bytes(
            [x if x != 0x95 else 0x9D for x in syscall_ctx.vm_ctx.rodata]
        )
        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        with open(f"{OUTPUT_DIR}/{testname}/v3/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
