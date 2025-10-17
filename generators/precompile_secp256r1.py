import fd58
import hashlib
import test_suite.protos.context_pb2 as context_pb
import test_suite.protos.txn_pb2 as txn_pb
from dataclasses import dataclass
import binascii
import requests
import json

OUTPUT_DIR = "./test-vectors/txn/tests/precompile/secp256r1"

program_id = "Secp256r1SigVerify1111111111111111111111111"
accounts = []

msg0 = bytes("hello", "ascii")
x = bytes.fromhex("d8c82b3791c8b51cfe44aa50226217159596ca26e6075aaf8bf8be2d351b96ae")
pub0 = bytes([2]) + x
r = bytes.fromhex("a940d67c9560a47c5dafb45ab1f39eb68c8fac9b51fc8c4e30b1f0e63e4967d3")
s = bytes.fromhex("586569a56364c3b03eefd421aa7fc750f6fa187210c3206c55602f96e0ecaa4d")
sig0 = r + s

msg = bytes.fromhex("deadbeef0002")
r = bytes.fromhex("16b60d19ba508f8bdac4c768bc868b9d2d458fc1c61a94af9423f6f850970eeb")
s = bytes.fromhex("3c18d9642122ce6f02c1a9b2a489feb3862e9682f21ea0c7c70a839ea2152f92")
x = bytes.fromhex("7929da089cf19abefaa8c13ade1de9b1c01291a261ebe9ae9a8f798936d56592")
y = bytes.fromhex("d46cb01e60e978e0a19730b6be922ecaec6e4f2e78707b6b3ead2453503bb111")
pub = bytes([3]) + x
sig = r + s

offset0 = len(pub0 + sig0 + msg0)

# fmt: off
test_vectors_agave = [
    # InvalidDataOffsets (result: 4)
    # invalid offset
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    # invalid data offset
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 99, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 1, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 232, 3, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255, 0, 0],
    # invalid pubkey offset
    [1, 0, 0, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 69, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # invalid signature offset
    [1, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 37, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # Ok() (result: 0)
    # valid signature
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg0), 0, 255, 255] + list(pub0) + list(sig0) + list(msg0),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig) + list(msg),
    [2, 0] + [63, 0, 255, 255, 30, 0, 255, 255, 127, 0, len(msg0), 0, 255, 255] + [63+offset0, 0, 255, 255, 30+offset0, 0, 255, 255, 127+offset0, 0, len(msg), 0, 255, 255] + list(pub0) + list(sig0) + list(msg0) + list(pub) + list(sig) + list(msg),
]


zero   = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")
n      = bytes.fromhex("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551")
n_half = bytes.fromhex("7fffffff800000007fffffffffffffffde737d56d38bcf4279dce5617e3192a8")

sig_r_0 = zero + s
sig_r_n = n + s
sig_s_0 = r + zero
sig_s_n = r + n
sig_s_n_half = r + n_half

pub_0 = bytes([0]) + x
pub_1 = bytes([1]) + x
pub_4 = bytes([4]) + x
pub_5 = bytes([5]) + x

pub_4_valid = pub_4 + y

# manual code cov
test_vectors_manual = [
    # InvalidInstructionDataSize
    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L185-L187
    [0],
    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L189-L191
    [0, 0],
    [0, 2],
    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L192-L194
    [9, 0],
    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L201-L203
    [1],
    [0, 0, 0],
    [1, 0, 0],
    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L259-L262

    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L265-L272
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig_r_0) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig_r_n) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig_s_0) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig_s_n) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub) + list(sig_s_n_half) + list(msg),

    # https://github.com/anza-xyz/agave/blob/v2.1.4/sdk/secp256r1-program/src/lib.rs#L279-L284
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub_0) + list(sig) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub_1) + list(sig) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub_4) + list(sig) + list(msg),
    [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0] + [len(msg), 0, 255, 255] + list(pub_5) + list(sig) + list(msg),

    [1, 0, 81, 0, 255, 255, 16, 0, 255, 255, 145, 0] + [len(msg), 0, 255, 255] + list(pub_4_valid) + list(sig) + list(msg),
]
# fmt: on


# test vectors from wycheproofs and cctv
@dataclass
class EddsaVerify:
    tcId: int
    comment: str
    msg: bytes
    sig: bytes
    pub: bytes
    ok: bool
    strict: bool


def simd_tests(name, max_lines=200):
    req = requests.get(
        f"https://raw.githubusercontent.com/Bunkr-2FA/SIMD-48-Testing/refs/heads/main/test_vectors/vectors_{name}.jsonl"
    )
    tests = []
    n = int.from_bytes(
        bytes.fromhex(
            "ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551"
        ),
        byteorder="big",
    )
    n_half = (n - 1) // 2
    for j, line in enumerate(req.iter_lines()):
        test = json.loads(line)
        r = bytes.fromhex(test.get("r"))
        s = bytes.fromhex(test.get("s"))
        s_int = int.from_bytes(s, byteorder="big")
        s_norm = s_int if s_int <= n_half else n - s_int
        if s_norm < 0:
            continue
        s_norm = s_norm.to_bytes(32, "big")
        x = bytes.fromhex(test.get("x"))
        y = bytes.fromhex(test.get("y"))
        y_last_byte_mod2 = y[len(y) - 1] % 2
        msg = bytes.fromhex(test.get("msg"))

        # print("-------")
        # print("r = ", binascii.hexlify(r))
        # print("s = ", binascii.hexlify(s))
        # print("x = ", binascii.hexlify(x))
        # print("y = ", binascii.hexlify(y))
        # print("pub = ", binascii.hexlify(bytes([2 + y_last_byte_mod2]) + x))
        # print("msg = ", binascii.hexlify(msg))

        tests.append(
            {
                "sig": r + s_norm,
                "pub": bytes([2 + y_last_byte_mod2]) + x,
                "msg": msg,
            }
        )
        if j < 5:
            tests.append(
                {
                    "sig": r + s_norm,
                    "pub": bytes([3 - y_last_byte_mod2]) + x,
                    "msg": msg,
                }
            )

        if j >= max_lines:
            break
    return tests


def simd_tests_wycheproof():
    req = requests.get(
        f"https://raw.githubusercontent.com/Bunkr-2FA/SIMD-48-Testing/refs/heads/main/test_vectors/vectors_wycheproof.jsonl"
    )
    tests = []
    for line in req.iter_lines():
        test = json.loads(line)
        r = bytes.fromhex(test.get("r"))
        s = bytes.fromhex(test.get("s"))
        x = bytes.fromhex(test.get("x"))
        y = bytes.fromhex(test.get("y"))
        y_last_byte_mod2 = y[len(y) - 1] % 2
        msg = bytes.fromhex(test.get("msg"))

        if len(r) != 32:
            print("len r")
        if len(s) != 32:
            print("len s")
        if len(x) != 32:
            print("len x")

        tests.append(
            {
                "sig": r + s,
                "pub": bytes([2 + y_last_byte_mod2]) + x,
                "msg": msg,
            }
        )
    return tests


# fmt: off
cache = {}
def _into_instr_data(key_prefix, verify_tests):
    test_vectors = []
    prefix = [1, 0, 49, 0, 255, 255, 16, 0, 255, 255, 113, 0]
    for j, test in enumerate(verify_tests):
        pub = test.get("pub")
        sig = test.get("sig")
        msg = test.get("msg")
        k = pub+sig+msg
        if k in cache:
            continue
        else:
            cache[k] = True
        l = len(msg)
        if l >= 1 << 16:
            print("msg too long, skipping")
            continue
        data = (
            prefix
            + [l % 256, l >> 8, 255, 255]
            + list(pub)
            + list(sig)
            + list(msg)
        )
        key = key_prefix + str(j)
        test_vectors.append((key, data))
    return test_vectors
# fmt: on


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


print("Generating secp256r1 tests...")

test_vectors = (
    _into_key_data("a", test_vectors_agave)
    + _into_key_data("m", test_vectors_manual)
    + _into_instr_data("vm", simd_tests("random_mixed", 3))
    + _into_instr_data("w", simd_tests_wycheproof())
)

program_id = fd58.dec32(bytes(program_id, "utf-8"))

signer = fd58.dec32(bytes("BWbmXj5ckAaWCAtzMZ97qnJhBAKegoXtgNrv9BUpAB11", "utf-8"))
signer_owner = bytes([0] * 32)
signer_lamports = 1_000_000_000

for key, test in test_vectors:
    txn_ctx = txn_pb.TxnContext()

    txn_ctx.tx.message.account_keys.extend(
        [
            signer,
            program_id,
        ]
    )

    signer_account = context_pb.AcctState()
    signer_account.address = signer
    signer_account.owner = signer_owner
    signer_account.lamports = signer_lamports
    txn_ctx.tx.message.account_shared_data.extend([signer_account])

    ix = txn_pb.CompiledInstruction()
    ix.program_id_index = 1
    ix.data = bytes(test)
    txn_ctx.tx.message.instructions.extend([ix])

    txn_ctx.epoch_ctx.features.features.extend(
        [
            0x2C38E34FF071060D,  # enable_secp256r1_precompile
        ]
    )

    serialized_txn = txn_ctx.SerializeToString(deterministic=True)
    filename = str(key) + "_" + hashlib.sha3_256(serialized_txn).hexdigest()[:16]
    with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
        f.write(serialized_txn)

print("done!")
