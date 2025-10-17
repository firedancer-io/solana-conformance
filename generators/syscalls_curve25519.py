import base64
import hashlib
import test_suite.protos.vm_pb2 as pb

OUTPUT_DIR = "./test-vectors/syscall/tests/curve25519"
HEAP_START = 0x300000000

CURVE_EDWARDS = 0
CURVE_RISTRETTO = 1

VAL_CU = lambda CURVE_RI: 169 if CURVE_RI else 159

ADD_OP = 0
ADD_CU = lambda CURVE_RI: 521 if CURVE_RI else 473

SUB_OP = 1
SUB_CU = lambda CURVE_RI: 519 if CURVE_RI else 475

MUL_OP = 2
MUL_CU = lambda CURVE_RI: 2_208 if CURVE_RI else 2_177

MSM_CU_BASE = lambda CURVE_RI: 2_303 if CURVE_RI else 2_273
MSM_CU_INCR = lambda CURVE_RI: 788 if CURVE_RI else 758

FEAT_GATE_ABORT_INVALID = 0xAFE148AD652172DD


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


valid_point = [
    [
        "c9b3f17ab4b9ef32b734dd0099c32b121626bbceb3c0d23a352d966259119e0b",  # rust: validate
        "217c47aa754597f73b0c5f7d85a64005021b5a1bc8a73ba4343634c81d0d22d5",  # rust: group_op
        # "46de89ddfdcc47334e087c0143c866e17ae46fb7810e83d2d45f6df6370a9f5b",  # rust: group_op
        # "fc1fe62ead5f90949e9d3f0a08443ab08ec0a8353d69c2a62b38f6ec1c927285",  # rust: msm
        # "0a6f08ec61bd7c4559b0de27c7fd6f0bf8ba805a7880f8d2e8b75d686f9607f1",  # rust: msm
    ],
    [
        "e2f2ae0a6abc4e71a884a961c500515f58e30b6aa582dd8db6a65945e08d2d76",  # rust: validate
        "d0a57dcc0264da11aac21709669c8688d9be6222b7c2e4995c0b6c671c39580f",  # rust: group_op
        # "d0f148a3493520ae36c2470846b5f4c75d9363e7a27f192827138c8470d4916c",  # rust: group_op
        # "8223611912c721ef558f776f3133e028a7b9f0b319c2d5290e9b6812b5c50f70",  # rust: msm
        # "989c9bc598e85ccedb9fc18679808b2438bf338f48cc574c6e7c6560ee9e2a6c",  # rust: msm
    ],
]

invalid_point = [
    "788c98e929e3cb1b577319fbdb0554947526543c5790a1922a225b9b9ebd794f",  # rust
]

scalar_valid = "fec6178a43f3b86eec73eccdcdd74f722dfa4e89036b88ed317e75df25bf5806"
scalar_invalid = "ffc6178a43f3b86eec73eccdcdd74f722dfa4e89036b88ed317e75df25bf58ff"

annoying_scalars = [
    "0000000000000000000000000000000000000000000000000000000000000000",  # 0
    "0100000000000000000000000000000000000000000000000000000000000000",  # 1
    "1000000000000000000000000000000014def9dea2f79cd65812631a5cf5d3ec",  # l-1
    "1000000000000000000000000000000014def9dea2f79cd65812631a5cf5d3ed",  # l == 0
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # ff
]

annoying_points = [
    "0100000000000000000000000000000000000000000000000000000000000000",  # ( 0    :  1   )  P0: order 1
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",  # ( 0    : -1   )  P1: order 2
    "0000000000000000000000000000000000000000000000000000000000000000",  # ( b0.. :  0   )  P2: order 4
    "0000000000000000000000000000000000000000000000000000000000000080",  # ( 3d.. :  0   ) -P2: order 4
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",  # ( 4a.. : 26.. )  P3: order 8
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",  # ( a3.. : 26.. ) -P3: order 8
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",  # ( 4a.. : c7.. )  P4: order 8
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",  # ( a3.. : c7.. ) -P4: order 8
    "0100000000000000000000000000000000000000000000000000000000000080",  # extra msb
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # extra msb
]

test_vectors_validate = [
    # EDWARDS
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L906
    # success
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_EDWARDS),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L910
    # not enough CU
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_EDWARDS) - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L912-L916
    # invalid memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "point_addr": HEAP_START + 1,
        "cu_avail": VAL_CU(CURVE_EDWARDS),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L921
    # invalid point
    {
        "heap_prefix": base64.b16decode(
            invalid_point[0],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_EDWARDS),
    },
    # RISTRETTO
    # success
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_RISTRETTO),
    },
    # not enough CU
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_RISTRETTO) - 1,
    },
    # invalid memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "point_addr": HEAP_START + 1,
        "cu_avail": VAL_CU(CURVE_RISTRETTO),
    },
    # invalid point
    {
        "heap_prefix": base64.b16decode(
            invalid_point[0],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_RISTRETTO),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L942-L950
    # invalid curve
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0],
            True,
        ),
        "curve_id": 2,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_EDWARDS),
    },
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0],
            True,
        ),
        "curve_id": 2,
        "point_addr": HEAP_START,
        "cu_avail": VAL_CU(CURVE_EDWARDS),
        "extra_features": [FEAT_GATE_ABORT_INVALID],
    },
]

test_vectors_op_invalid = [
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1058-L1065
    # invalid op ed
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0] + valid_point[CURVE_EDWARDS][1],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "group_op": 3,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_EDWARDS),
    },
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_EDWARDS][0] + valid_point[CURVE_EDWARDS][1],
            True,
        ),
        "curve_id": CURVE_EDWARDS,
        "group_op": 3,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_EDWARDS),
        "extra_features": [FEAT_GATE_ABORT_INVALID],
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1156-L1165
    # invalid op ri
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0] + valid_point[CURVE_RISTRETTO][1],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "group_op": 3,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_RISTRETTO),
    },
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0] + valid_point[CURVE_RISTRETTO][1],
            True,
        ),
        "curve_id": CURVE_RISTRETTO,
        "group_op": 3,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_RISTRETTO),
        "extra_features": [FEAT_GATE_ABORT_INVALID],
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1168-L1177
    # invalid curve
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0] + valid_point[CURVE_RISTRETTO][1],
            True,
        ),
        "curve_id": 2,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_RISTRETTO),
    },
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE_RISTRETTO][0] + valid_point[CURVE_RISTRETTO][1],
            True,
        ),
        "curve_id": 2,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE_RISTRETTO),
        "extra_features": [FEAT_GATE_ABORT_INVALID],
    },
]

test_vectors_add = lambda CURVE: [
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L973
    # success
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L977
    # not enough CU
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE) - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L979-L983
    # invalid left point - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START + 100,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L984-L988
    # invalid right point - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 132,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L991-L995
    # invalid result - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START + 33,
        "cu_avail": ADD_CU(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L998
    # invalid left point
    {
        "heap_prefix": base64.b16decode(
            invalid_point[0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE),
    },
    # invalid right point
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + invalid_point[0],
            True,
        ),
        "curve_id": CURVE,
        "group_op": ADD_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": ADD_CU(CURVE),
    },
]

test_vectors_sub = lambda CURVE: [
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1001
    # success
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE),
    },
    # not enough CU
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE) - 1,
    },
    # invalid left point - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START + 100,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE),
    },
    # invalid right point - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 132,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE),
    },
    # invalid result - memory mapping
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START + 33,
        "cu_avail": SUB_CU(CURVE),
    },
    # invalid left point
    {
        "heap_prefix": base64.b16decode(
            invalid_point[0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE),
    },
    # invalid right point
    {
        "heap_prefix": base64.b16decode(
            valid_point[CURVE][0] + invalid_point[0],
            True,
        ),
        "curve_id": CURVE,
        "group_op": SUB_OP,
        "left_input_addr": HEAP_START,
        "right_input_addr": HEAP_START + 32,
        "result_point_addr": HEAP_START,
        "cu_avail": SUB_CU(CURVE),
    },
]

test_vectors_mul = (
    lambda CURVE: [
        # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L973
        # success
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
        # not enough CU
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE) - 1,
        },
        # invalid left scalar - memory mapping
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START + 100,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
        # invalid right point - memory mapping
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 132,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
        # invalid result - memory mapping
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START + 33,
            "cu_avail": MUL_CU(CURVE),
        },
        # invalid left scalar
        {
            "heap_prefix": base64.b16decode(
                scalar_invalid + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
        # invalid right point
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + invalid_point[0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
        # invert scalar & point (not that it matters but...)
        {
            "heap_prefix": base64.b16decode(
                valid_point[CURVE][0] + scalar_valid,
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        },
    ]
    + [
        {
            "heap_prefix": base64.b16decode(
                scalar + valid_point[CURVE][0],
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        }
        for scalar in annoying_scalars
    ]
    + [
        {
            "heap_prefix": base64.b16decode(
                scalar_valid + point,
                True,
            ),
            "curve_id": CURVE,
            "group_op": MUL_OP,
            "left_input_addr": HEAP_START,
            "right_input_addr": HEAP_START + 32,
            "result_point_addr": HEAP_START,
            "cu_avail": MUL_CU(CURVE),
        }
        for point in annoying_points
    ]
)

MSM_LEN = 2
test_vectors_msm = lambda CURVE: [
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1198-L1200
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START,
        "points_len": 513,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1203
    # success
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START + MSM_LEN * 32,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1213
    # not enough CU
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START + MSM_LEN * 32,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE) - 1,
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1215-L1220
    # invalid scalars - memory mapping
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START + 100,
        "points_addr": HEAP_START + MSM_LEN * 32,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1222-L1227
    # invalid points - memory mapping
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START + MSM_LEN * 32 + 1,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1237
    # invalid point
    {
        "heap_prefix": base64.b16decode(
            scalar_valid + scalar_valid + valid_point[CURVE][0] + invalid_point[0],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
    # invalid scalar
    {
        "heap_prefix": base64.b16decode(
            scalar_valid
            + scalar_invalid
            + valid_point[CURVE][0]
            + valid_point[CURVE][1],
            True,
        ),
        "curve_id": CURVE,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE) + (MSM_LEN - 1) * MSM_CU_INCR(CURVE),
    },
]

test_vectors_msm_invalid = [
    # https://github.com/anza-xyz/agave/blob/v2.0.3/programs/bpf_loader/src/syscalls/mod.rs#L1281-L1290
    {
        "heap_prefix": base64.b16decode(
            scalar_valid
            + scalar_valid
            + valid_point[CURVE_EDWARDS][0]
            + valid_point[CURVE_EDWARDS][1],
            True,
        ),
        "curve_id": 2,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE_EDWARDS)
        + (MSM_LEN - 1) * MSM_CU_INCR(CURVE_EDWARDS),
    },
    {
        "heap_prefix": base64.b16decode(
            scalar_valid
            + scalar_valid
            + valid_point[CURVE_EDWARDS][0]
            + valid_point[CURVE_EDWARDS][1],
            True,
        ),
        "curve_id": 2,
        "scalars_addr": HEAP_START,
        "points_addr": HEAP_START,
        "points_len": MSM_LEN,
        "result_point_addr": HEAP_START,
        "cu_avail": MSM_CU_BASE(CURVE_EDWARDS)
        + (MSM_LEN - 1) * MSM_CU_INCR(CURVE_EDWARDS),
        "extra_features": [FEAT_GATE_ABORT_INVALID],
    },
]

test_vectors_validate = _into_key_data("val", test_vectors_validate)

test_vectors_group = (
    _into_key_data("inv", test_vectors_op_invalid)
    + _into_key_data("add_ed", test_vectors_add(CURVE_EDWARDS))
    + _into_key_data("add_ri", test_vectors_add(CURVE_RISTRETTO))
    + _into_key_data("sub_ed", test_vectors_sub(CURVE_EDWARDS))
    + _into_key_data("sub_ri", test_vectors_sub(CURVE_RISTRETTO))
    + _into_key_data("mul_ed", test_vectors_mul(CURVE_EDWARDS))
    + _into_key_data("mul_ri", test_vectors_mul(CURVE_RISTRETTO))
)

test_vectors_msm = (
    _into_key_data("msm_inv", test_vectors_msm_invalid)
    + _into_key_data("msm_ed", test_vectors_msm(CURVE_EDWARDS))
    + _into_key_data("msm_ri", test_vectors_msm(CURVE_RISTRETTO))
)

if __name__ == "__main__":
    print("Generating syscall curve25519 sol_curve_validate_point tests...")

    for key, test in test_vectors_validate:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_curve_validate_point"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("curve_id", 0)
        syscall_ctx.vm_ctx.r2 = test.get("point_addr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.instr_ctx.epoch_context.features.features.extend(
            [
                0x4B1E586FC635DC65,  # curve25519_syscall_enabled
                # 0xafe148ad652172dd,  # abort_on_invalid_curve - added dynamically
            ]
            + test.get("extra_features", [])
        )

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")

    print("Generating syscall curve25519 sol_curve_group_op tests...")

    for key, test in test_vectors_group:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_curve_group_op"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("curve_id", 0)
        syscall_ctx.vm_ctx.r2 = test.get("group_op", 0)
        syscall_ctx.vm_ctx.r3 = test.get("left_input_addr", 0)
        syscall_ctx.vm_ctx.r4 = test.get("right_input_addr", 0)
        syscall_ctx.vm_ctx.r5 = test.get("result_point_addr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.instr_ctx.epoch_context.features.features.extend(
            [
                0x4B1E586FC635DC65,  # curve25519_syscall_enabled
                # 0xafe148ad652172dd,  # abort_on_invalid_curve - added dynamically
            ]
            + test.get("extra_features", [])
        )

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")

    print("Generating syscall curve25519 sol_curve_multiscalar_mul tests...")

    for key, test in test_vectors_msm:
        heap_prefix = test.get("heap_prefix", [])
        syscall_ctx = pb.SyscallContext()
        syscall_ctx.syscall_invocation.function_name = b"sol_curve_multiscalar_mul"
        syscall_ctx.syscall_invocation.heap_prefix = bytes(heap_prefix)
        syscall_ctx.vm_ctx.heap_max = len(heap_prefix)
        syscall_ctx.vm_ctx.r1 = test.get("curve_id", 0)
        syscall_ctx.vm_ctx.r2 = test.get("scalars_addr", 0)
        syscall_ctx.vm_ctx.r3 = test.get("points_addr", 0)
        syscall_ctx.vm_ctx.r4 = test.get("points_len", 0)
        syscall_ctx.vm_ctx.r5 = test.get("result_point_addr", 0)
        syscall_ctx.instr_ctx.cu_avail = test.get("cu_avail", 0)
        syscall_ctx.instr_ctx.program_id = bytes(
            [0] * 32
        )  # solfuzz-agave expectes a program_id

        syscall_ctx.instr_ctx.epoch_context.features.features.extend(
            [
                0x4B1E586FC635DC65,  # curve25519_syscall_enabled
                # 0xafe148ad652172dd,  # abort_on_invalid_curve - added dynamically
            ]
            + test.get("extra_features", [])
        )

        serialized_instr = syscall_ctx.SerializeToString(deterministic=True)
        filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
        with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
            f.write(serialized_instr)

    print("done!")
