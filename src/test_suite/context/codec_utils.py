import test_suite.context_pb2 as context_pb
import fd58
import re


def decode_hex_compact(encoded):
    res = bytearray()
    parts = re.split(r"\.\.\.(\d+) zeros\.\.\.", encoded.decode("ascii"))

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Regular hex part
            res.extend(bytes.fromhex(part))
        else:
            # Skipped zeros part
            res.extend(b"\x00" * int(part))

    return bytes(res)


def encode_hex_compact(buf, gap=16):
    res = ""
    skipped = 0
    for i in range(0, len(buf), gap):
        row = buf[i : i + gap]
        if row == bytes([0] * len(row)):
            skipped += len(row)
        else:
            if skipped > 0:
                res += f"...{skipped} zeros..."
            res += "".join([f"{b:0>2x}" for b in buf[i : i + gap]])
            skipped = 0
    if skipped > 0:
        res += f"...{skipped} zeros..."
    return bytes(res, "ascii")


def encode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.enc32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.enc32(acct_state.owner)

    # Data
    if acct_state.data:
        acct_state.data = encode_hex_compact(acct_state.data)


def decode_acct_state(acct_state: context_pb.AcctState):
    # Pubkey
    if acct_state.address:
        acct_state.address = fd58.dec32(acct_state.address)

    # Owner
    if acct_state.owner:
        acct_state.owner = fd58.dec32(acct_state.owner)

    # Data
    if acct_state.data:
        acct_state.data = decode_hex_compact(acct_state.data)
