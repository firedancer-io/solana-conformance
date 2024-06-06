import fd58
import hashlib
from eth_hash.auto import keccak
import test_suite.invoke_pb2 as pb
from dataclasses import dataclass
import requests

OUTPUT_DIR = "./test-vectors/precompile/tests/secp256k1"

program_id = "KeccakSecp256k11111111111111111111111111111"
accounts = []

# https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L1039
test_vectors_agave = [
    # test_count_is_zero_but_sig_data_exists
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # test_invalid_offsets
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0] + [ 0 ] * 100,
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1] + [ 0 ] * 100,
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0] + [ 0 ] * 100,
    # test_signature_offset
    [1, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 37, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # test_eth_offset
    [1, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 81, 0, 0, 0, 0, 0, 0, 0],
    # test_message_data_offsets
    [1, 0, 0, 0, 0, 0, 0, 99, 0, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 100, 0, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 100, 0, 232, 3, 0],
    [1, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255, 0],
    # test_secp256k1
    [1, 32, 0, 0, 12, 0, 0, 97, 0, 5, 0, 0, 129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101, 14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3, 1, 104, 101, 108, 108, 111],
    [1, 32, 12, 0, 12, 0, 0, 97, 0, 5, 0, 0, 129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101, 14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3, 1, 104, 101, 108, 108, 111],
    # test_malleability
    [2, 23, 0, 0, 88, 0, 0, 108, 0, 5, 0, 0, 113, 0, 0, 178, 0, 0, 198, 0, 5, 0, 0, 8, 106, 2, 17, 228, 135, 168, 210, 219, 113, 75, 102, 239, 51, 218, 230, 218, 125, 149, 73, 201, 61, 102, 253, 170, 115, 201, 14, 162, 243, 11, 22, 90, 90, 242, 118, 196, 38, 97, 5, 74, 132, 110, 172, 168, 204, 248, 224, 162, 249, 64, 95, 48, 88, 72, 56, 157, 16, 4, 2, 165, 47, 207, 113, 0, 45, 237, 4, 121, 189, 201, 77, 37, 225, 171, 23, 82, 196, 28, 174, 59, 124, 136, 139, 245, 104, 101, 108, 108, 111, 8, 106, 2, 17, 228, 135, 168, 210, 219, 113, 75, 102, 239, 51, 218, 230, 218, 125, 149, 73, 201, 61, 102, 253, 170, 115, 201, 14, 162, 243, 11, 22, 165, 165, 13, 137, 59, 217, 158, 250, 181, 123, 145, 83, 87, 51, 7, 30, 23, 181, 156, 135, 126, 240, 88, 3, 34, 194, 90, 138, 43, 6, 113, 208, 1, 45, 237, 4, 121, 189, 201, 77, 37, 225, 171, 23, 82, 196, 28, 174, 59, 124, 136, 139, 245, 104, 101, 108, 108, 111],
]

prefix     = [1, 32, 0, 0, 12, 0, 0, 97, 0, 5, 0, 0]
prefix_alt = [1, 37, 0, 0, 12, 0, 0, 32, 0, 5, 0, 0]  ## swap sig, msg
pubkey =     [129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101]
pubkey_err = [111, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101]
sig =         [14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3]
sig_invalid = [255]*64
sig_err     = [14, 196, 198, 193, 237, 0, 14, 255, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3]
#                                             ^^^ modified byte
recid = 1
msg = [104, 101, 108, 108, 111]  # hello

# manual code cov
test_vectors_manual = [
    # inconsistent between ed25519 and secp256k1
    [ 0 ],    # ed25519: err, secp256k1: ok
    [ 0, 0 ], # ed25519: ok,  secp256k1: err
    [ 0, 2 ], # ed25519: ok,  secp256k1: err
    # InvalidInstructionDataSize (result: 5)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L937-L947
    # note: this is different behavior than ed25519
    [],
    [ 0, 0, 0 ],

    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L951-L953
    [ 1 ],
    [ 1, 0, 0 ],

    # InvalidSignature (result: 3)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L960-L961
    # ??? I don't think this can ever happen?

    # InvalidDataOffsets (result: 4)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L965-L967
    # tested above

    # InvalidSignature (result: 3)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L971-L973
    # tested above
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L975-L978
    # signature fails to decode
    [1, 32, 0, 0, 12, 0, 0, 97, 0, 5, 0, 0, 129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101, 255, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3, 1, 104, 101, 108, 108, 111],
    #                                       \--- pubkey (eth)                                                                     ---/  \--- sig                                                                                                                                                                                                                                                                                       ---/  \--- msg           ---/

    # InvalidRecoveryId (result: 2)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L981C43-L981C60
    prefix + pubkey + sig + [4] + msg,
    prefix_alt + pubkey + msg + sig + [4],
    prefix_alt + pubkey + msg + sig,

    # InvalidDataOffsets (result: 4)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L984-L989
    # tested above
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L992-L997
    # tested above

    # InvalidSignature (result: 3)
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L1003-L1008
    # signature fails to verify
    [1, 32, 0, 0, 12, 0, 0, 97, 0, 5, 0, 0, 129, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101, 14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3, 1, 104, 101, 108, 108, 255],
    [2, 23, 0, 0, 88, 0, 0, 108, 0, 5, 0, 0, 113, 0, 0, 178, 0, 0, 198, 0, 5, 0, 0, 8, 106, 2, 17, 228, 135, 168, 210, 219, 113, 75, 102, 239, 51, 218, 230, 218, 125, 149, 73, 201, 61, 102, 253, 170, 115, 201, 14, 162, 243, 11, 22, 90, 90, 242, 118, 196, 38, 97, 5, 74, 132, 110, 172, 168, 204, 248, 224, 162, 249, 64, 95, 48, 88, 72, 56, 157, 16, 4, 2, 165, 47, 207, 113, 0, 45, 237, 4, 121, 189, 201, 77, 37, 225, 171, 23, 82, 196, 28, 174, 59, 124, 136, 139, 245, 104, 101, 108, 108, 111, 8, 106, 2, 17, 228, 135, 168, 210, 219, 113, 75, 102, 239, 51, 218, 230, 218, 125, 149, 73, 201, 61, 102, 253, 170, 115, 201, 14, 162, 243, 11, 22, 165, 165, 13, 137, 59, 217, 158, 250, 181, 123, 145, 83, 87, 51, 7, 30, 23, 181, 156, 135, 126, 240, 88, 3, 34, 194, 90, 138, 43, 6, 113, 208, 1, 45, 237, 4, 121, 189, 201, 77, 37, 225, 171, 23, 82, 196, 28, 174, 59, 124, 136, 139, 245, 104, 101, 108, 108, 255],
    # https://github.com/anza-xyz/agave/blob/v1.18.12/sdk/src/secp256k1_instruction.rs#L1003-L1008
    # sig returns incorrect pubkey
    [1, 32, 0, 0, 12, 0, 0, 97, 0, 5, 0, 0, 111, 246, 169, 169, 105, 76, 208, 128, 223, 135, 27, 68, 249, 42, 201, 69, 55, 2, 173, 101, 14, 196, 198, 193, 237, 0, 14, 83, 87, 183, 25, 69, 136, 43, 251, 73, 44, 194, 141, 230, 102, 16, 220, 6, 46, 214, 214, 125, 120, 16, 103, 254, 39, 121, 88, 223, 156, 229, 186, 211, 38, 101, 196, 233, 125, 150, 136, 177, 123, 197, 48, 219, 28, 26, 10, 76, 198, 127, 91, 80, 88, 191, 6, 3, 1, 104, 101, 108, 108, 111],
    #                                       \--- pubkey (eth)                                                                     ---/  \--- sig                                                                                                                                                                                                                                                                                      ---/  \--- msg           ---/
]

def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]

print("Generating secp256k1 tests...")

test_vectors = _into_key_data("a", test_vectors_agave) \
    + _into_key_data("m", test_vectors_manual)

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
    instr_ctx.epoch_context.features.features.extend([0x1a6958db2ff09870])

    serialized_instr = instr_ctx.SerializeToString(deterministic=True)
    filename = str(key) + "_" + hashlib.sha3_256(serialized_instr).hexdigest()[:16]
    with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
        f.write(serialized_instr)

print("done!")
