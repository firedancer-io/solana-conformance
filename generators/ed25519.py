import fd58
import hashlib
import test_suite.invoke_pb2 as pb
from dataclasses import dataclass
import requests

OUTPUT_DIR = "./test-vectors/instr/inputs/20240425/ed25519"

program_id = "Ed25519SigVerify111111111111111111111111111"
accounts = []

# https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L181
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
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 75, 214, 129, 151, 244, 149, 70, 192, 102, 135, 224, 99, 199, 172, 238, 204, 3, 67, 253, 92, 104, 212, 24, 116, 243, 199, 49, 42, 20, 156, 143, 83, 1, 148, 145, 203, 46, 109, 182, 75, 135, 218, 65, 3, 176, 77, 9, 53, 33, 86, 42, 178, 80, 169, 11, 169, 251, 61, 180, 51, 167, 39, 34, 189, 140, 51, 151, 209, 50, 76, 167, 90, 205, 1, 57, 197, 149, 97, 99, 241, 191, 66, 222, 90, 0, 251, 220, 145, 101, 24, 220, 32, 183, 0, 19, 5, 104, 101, 108, 108, 111],
    # InvalidPublicKey (result: 1)
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 75, 214, 129, 151, 0, 149, 70, 192, 102, 135, 224, 99, 199, 172, 238, 204, 3, 67, 253, 92, 104, 212, 24, 116, 243, 199, 49, 42, 20, 156, 143, 83, 1, 148, 145, 203, 46, 109, 182, 75, 135, 218, 65, 3, 176, 77, 9, 53, 33, 86, 42, 178, 80, 169, 11, 169, 251, 61, 180, 51, 167, 39, 34, 189, 140, 51, 151, 209, 50, 76, 167, 90, 205, 1, 57, 197, 149, 97, 99, 241, 191, 66, 222, 90, 0, 251, 220, 145, 101, 24, 220, 32, 183, 0, 19, 5, 104, 101, 108, 108, 111]
]

# manual code cov
test_vectors_manual = [
    # inconsistent between ed25519 and secp256k1
    [ 0 ],    # ed25519: err, secp256k1: ok
    [ 0, 0 ], # ed25519: ok,  secp256k1: err
    [ 0, 2 ], # ed25519: ok,  secp256k1: err
    # InvalidInstructionDataSize (result: 5)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L90-L92
    [ 1 ],
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L94-L96
    [ 0, 0, 0 ],
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L101-L103
    [ 1, 0, 0 ],

    # InvalidDataOffsets (result: 4)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L111-L112
    # ???
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L115-L121
    # tested above

    # InvalidSignature (result: 3)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L123-L124
    # signature fails to decode
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 255, 104, 101, 108, 108, 111],

    # InvalidDataOffsets (result: 4)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L127-L133
    # tested above

    # InvalidPublicKey (result: 1)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L135-L136
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 88, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 9, 104, 101, 108, 108, 111],

    # InvalidDataOffsets (result: 4)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L139-L145
    # tested above

    # InvalidSignature (result: 3)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/ed25519_instruction.rs#L147-L149
    # signature fails to verify
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 16, 104, 101, 108, 108, 111],
    [2, 0, 62, 0, 255, 255, 30, 0, 255, 255, 126, 0, 5, 0, 255, 255,
           163, 0, 255, 255, 131, 0, 255, 255, 227, 0, 5, 0, 255, 255,
           77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 9, 104, 101, 108, 108, 111,
           75, 214, 129, 151, 244, 149, 70, 192, 102, 135, 224, 99, 199, 172, 238, 204, 3, 67, 253, 92, 104, 212, 24, 116, 243, 199, 49, 42, 20, 156, 143, 83, 1, 148, 145, 203, 46, 109, 182, 75, 135, 218, 65, 3, 176, 77, 9, 53, 33, 86, 42, 178, 80, 169, 11, 169, 251, 61, 180, 51, 167, 39, 34, 189, 140, 51, 151, 209, 50, 76, 167, 90, 205, 1, 57, 197, 149, 97, 99, 241, 191, 66, 222, 90, 0, 251, 220, 145, 101, 24, 220, 32, 183, 0, 19, 16, 104, 101, 108, 108, 111],

    # Ok()
    # valid
    [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, 5, 0, 255, 255, 77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 9, 104, 101, 108, 108, 111],
    # valid (add 14 to offsets, dupe the struct)
    [2, 0, 62, 0, 255, 255, 30, 0, 255, 255, 126, 0, 5, 0, 255, 255,
           62, 0, 255, 255, 30, 0, 255, 255, 126, 0, 5, 0, 255, 255, 77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 9, 104, 101, 108, 108, 111],
    # 2 valid
    [2, 0, 62, 0, 255, 255, 30, 0, 255, 255, 126, 0, 5, 0, 255, 255,
           163, 0, 255, 255, 131, 0, 255, 255, 227, 0, 5, 0, 255, 255,
           77, 24, 168, 156, 166, 0, 87, 128, 189, 248, 212, 58, 28, 154, 34, 186, 179, 37, 7, 189, 36, 105, 135, 255, 37, 58, 68, 162, 199, 239, 98, 214, 47, 43, 230, 141, 139, 231, 170, 75, 55, 76, 78, 200, 97, 43, 17, 24, 225, 143, 160, 169, 12, 27, 16, 219, 4, 218, 114, 30, 149, 132, 33, 178, 94, 40, 150, 10, 243, 203, 248, 194, 243, 66, 51, 212, 101, 196, 7, 121, 101, 161, 171, 161, 88, 6, 129, 191, 191, 157, 230, 170, 180, 16, 67, 9, 104, 101, 108, 108, 111,
           75, 214, 129, 151, 244, 149, 70, 192, 102, 135, 224, 99, 199, 172, 238, 204, 3, 67, 253, 92, 104, 212, 24, 116, 243, 199, 49, 42, 20, 156, 143, 83, 1, 148, 145, 203, 46, 109, 182, 75, 135, 218, 65, 3, 176, 77, 9, 53, 33, 86, 42, 178, 80, 169, 11, 169, 251, 61, 180, 51, 167, 39, 34, 189, 140, 51, 151, 209, 50, 76, 167, 90, 205, 1, 57, 197, 149, 97, 99, 241, 191, 66, 222, 90, 0, 251, 220, 145, 101, 24, 220, 32, 183, 0, 19, 5, 104, 101, 108, 108, 111],
]

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

def wycheproofs_ed25519():
    req = requests.get(
        "https://raw.githubusercontent.com/google/wycheproof/master/testvectors/eddsa_test.json"
    )
    assert req.status_code == 200
    file = req.json()
    assert file["algorithm"] == "EDDSA"
    assert file["schema"] == "eddsa_verify_schema.json"
    verify_tests = []
    for group in file["testGroups"]:
        if group["type"] != "EddsaVerify":
            print(f"Skipping {group['type']} test")
            continue
        pubkey = bytes.fromhex(group["key"]["pk"])
        for test in group["tests"]:
            verify_tests.append(
                EddsaVerify(
                    tcId=test["tcId"],
                    comment=test["comment"],
                    msg=bytes.fromhex(test["msg"]),
                    sig=bytes.fromhex(test["sig"]),
                    pub=pubkey,
                    ok=test["result"] == "valid",
                    strict=test["result"] == "valid",
                )
            )
    return verify_tests

def cctv_ed25519():
    req = requests.get(
        "https://raw.githubusercontent.com/C2SP/CCTV/main/ed25519/ed25519vectors.json"
    )
    assert req.status_code == 200
    file = req.json()
    verify_tests = []
    for test in file:
        flags = test["flags"]
        if flags:
            set_flags = set(flags)
            ok = (set_flags - set(["low_order_A", "low_order_R", "non_canonical_A", "low_order_component_A", "low_order_component_R", "reencoded_k"])) == set()
            strict = (set_flags - set(["low_order_component_A", "low_order_component_R"])) == set()
            if "non_canonical_R" in set_flags and "low_order_R" not in set_flags:
                raise Exception(test["number"])
        else:
            ok = True
            strict = True
        verify_tests.append(
            EddsaVerify(
                tcId=test["number"],
                comment=test["msg"],
                msg=bytes(test["msg"], 'utf-8'),
                sig=bytes.fromhex(test["sig"]),
                pub=bytes.fromhex(test["key"]),
                ok=ok,  # we implement dalek verify_strict, so all these should fail
                strict=strict,
            )
        )
    return verify_tests

def _into_instr_data(key_prefix, verify_tests):
    test_vectors = []
    prefix = [1, 0, 48, 0, 255, 255, 16, 0, 255, 255, 112, 0, ]
    for test in verify_tests:
        l = len(test.msg)
        if l >= 1<<16:
            print("msg too long, skipping")
            continue
        data = prefix + [l % 256, l >> 8, 255, 255] + list(test.pub) + list(test.sig) + list(test.msg)
        key = key_prefix + str(test.tcId)
        test_vectors.append((key, data))
    return test_vectors

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]

print("Generating ed25519 tests...")

test_vectors = _into_key_data("a", test_vectors_agave) \
    + _into_key_data("m", test_vectors_manual) \
    + _into_instr_data("w", wycheproofs_ed25519()) \
    + _into_instr_data("c", cctv_ed25519())

program_id = fd58.dec32(bytes(program_id, "utf-8"))
program_owner = fd58.dec32(bytes("NativeLoader1111111111111111111111111111111", "utf-8"))
for (key, test) in test_vectors:
    instr_ctx = pb.InstrContext()
    instr_ctx.program_id = program_id
    instr_ctx.data = bytes(test)

    account = pb.AcctState()
    account.address = program_id
    account.owner = program_owner
    instr_ctx.accounts.extend([account])
    instr_ctx.instr_accounts.extend([pb.InstrAcct()])

    filename = str(key) + "_" + hashlib.sha3_256(instr_ctx.data).hexdigest()[:16]

    serialized_instr = instr_ctx.SerializeToString(deterministic=True)
    with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
        f.write(serialized_instr)

print("done!")
