"""
Generate gossip message deserialization test vectors.

Produces .gossipctx files containing GossipMessageBinary protobuf messages
wrapping raw bincode-encoded gossip Protocol variants. These are fed to
solana-conformance create-fixtures with -h GossipHarness to produce fixtures.

Usage:
    python3 generators/gossip.py
    solana-conformance create-fixtures \\
        -i ./test-vectors/gossip/tests \\
        -o ./test-vectors/gossip/fixtures \\
        -s $SOLFUZZ_TARGET -h GossipHarness
"""

import hashlib
import os
import struct
import sys

src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"
)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import test_suite.protos.gossip_pb2 as gossip_pb

OUTPUT_DIR = "./test-vectors/gossip/tests"

VARIANT_PULL_REQUEST = 0
VARIANT_PULL_RESPONSE = 1
VARIANT_PUSH_MESSAGE = 2
VARIANT_PRUNE_MESSAGE = 3
VARIANT_PING_MESSAGE = 4
VARIANT_PONG_MESSAGE = 5


def u32(v: int) -> bytes:
    return struct.pack("<I", v)


def u64(v: int) -> bytes:
    return struct.pack("<Q", v)


def pubkey(seed: int = 0) -> bytes:
    return bytes([(seed + i) & 0xFF for i in range(32)])


def signature(seed: int = 0) -> bytes:
    return bytes([(seed + i) & 0xFF for i in range(64)])


def hash32(seed: int = 0) -> bytes:
    return bytes([(seed + i * 7) & 0xFF for i in range(32)])


def make_bloom(num_keys: int = 3, num_blocks: int = 2, num_bits_set: int = 5) -> bytes:
    """Bloom<Hash> = { keys: Vec<u64>, bits: BitVec<u64>, num_bits_set: u64 }"""
    buf = bytearray()
    buf += u64(num_keys)
    for i in range(num_keys):
        buf += u64(0x1234567890ABCDEF + i)
    buf += u64(num_blocks)
    for i in range(num_blocks):
        buf += u64((1 << (i * 8)) | 0xFF)
    buf += u64(num_blocks * 64)  # bit_len
    buf += u64(num_bits_set)
    return bytes(buf)


def make_crds_filter(
    mask: int = 0, mask_bits: int = 0, bloom_keys: int = 3, bloom_blocks: int = 2
) -> bytes:
    """CrdsFilter = { filter: Bloom<Hash>, mask: u64, mask_bits: u32 }"""
    buf = bytearray()
    buf += make_bloom(num_keys=bloom_keys, num_blocks=bloom_blocks)
    buf += u64(mask)
    buf += u32(mask_bits)
    return bytes(buf)


def make_crds_value(
    crds_data_variant: int = 0, crds_data_payload: bytes = b""
) -> bytes:
    """CrdsValue = { signature: Signature(64), data: CrdsData }"""
    buf = bytearray()
    buf += signature(crds_data_variant)
    buf += u32(crds_data_variant)
    buf += crds_data_payload
    return bytes(buf)


def make_prune_data(num_prunes: int = 0) -> bytes:
    """PruneData = { pubkey(32), prunes: Vec<Pubkey>, signature(64), destination(32), wallclock(u64) }"""
    buf = bytearray()
    buf += pubkey(10)
    buf += u64(num_prunes)
    for i in range(num_prunes):
        buf += pubkey(20 + i)
    buf += signature(30)
    buf += pubkey(40)
    buf += u64(1700000000000)  # plausible wallclock
    return bytes(buf)


def make_ping(seed: int = 0) -> bytes:
    """Ping = { from: Pubkey(32), token: [u8; 32], signature(64) }"""
    return pubkey(seed) + hash32(seed + 50) + signature(seed + 100)


def make_pong(seed: int = 0) -> bytes:
    """Pong = { from: Pubkey(32), hash: Hash(32), signature(64) }"""
    return pubkey(seed) + hash32(seed + 60) + signature(seed + 110)


# ---- Test vectors ----

test_vectors = []

# -- Edge cases --
test_vectors.append(("edge_empty", b""))
test_vectors.append(("edge_1byte", b"\x00"))
test_vectors.append(("edge_3bytes", b"\x00\x00\x00"))
test_vectors.append(("edge_variant_only", u32(0)))
test_vectors.append(("edge_invalid_variant", u32(6)))
test_vectors.append(("edge_large_variant", u32(0xFFFFFFFF)))
test_vectors.append(("edge_max_size", u32(0) + bytes(1228)))

# -- PingMessage (variant 4) --
test_vectors.append(("ping_valid", u32(VARIANT_PING_MESSAGE) + make_ping(0)))
test_vectors.append(("ping_valid_2", u32(VARIANT_PING_MESSAGE) + make_ping(42)))
test_vectors.append(
    ("ping_truncated_no_sig", u32(VARIANT_PING_MESSAGE) + pubkey(0) + hash32(0))
)
test_vectors.append(
    (
        "ping_truncated_partial_sig",
        u32(VARIANT_PING_MESSAGE) + pubkey(0) + hash32(0) + signature(0)[:32],
    )
)
test_vectors.append(("ping_truncated_no_token", u32(VARIANT_PING_MESSAGE) + pubkey(0)))
test_vectors.append(
    ("ping_extra_bytes", u32(VARIANT_PING_MESSAGE) + make_ping(0) + bytes(16))
)

# -- PongMessage (variant 5) --
test_vectors.append(("pong_valid", u32(VARIANT_PONG_MESSAGE) + make_pong(0)))
test_vectors.append(("pong_valid_2", u32(VARIANT_PONG_MESSAGE) + make_pong(99)))
test_vectors.append(
    ("pong_truncated", u32(VARIANT_PONG_MESSAGE) + pubkey(0) + hash32(0))
)

# -- PruneMessage (variant 3) --
test_vectors.append(
    ("prune_empty_prunes", u32(VARIANT_PRUNE_MESSAGE) + pubkey(0) + make_prune_data(0))
)
test_vectors.append(
    ("prune_one_prune", u32(VARIANT_PRUNE_MESSAGE) + pubkey(0) + make_prune_data(1))
)
test_vectors.append(
    ("prune_five_prunes", u32(VARIANT_PRUNE_MESSAGE) + pubkey(0) + make_prune_data(5))
)
test_vectors.append(
    ("prune_max_prunes", u32(VARIANT_PRUNE_MESSAGE) + pubkey(0) + make_prune_data(20))
)
test_vectors.append(
    (
        "prune_truncated",
        u32(VARIANT_PRUNE_MESSAGE) + pubkey(0) + pubkey(10) + u64(1) + pubkey(20),
    )
)

# -- PullResponse (variant 1) --
test_vectors.append(
    ("pullresp_empty_vec", u32(VARIANT_PULL_RESPONSE) + pubkey(0) + u64(0))
)
test_vectors.append(
    (
        "pullresp_one_value",
        u32(VARIANT_PULL_RESPONSE)
        + pubkey(0)
        + u64(1)
        + make_crds_value(0, pubkey(80)),
    )
)
test_vectors.append(
    (
        "pullresp_two_values",
        u32(VARIANT_PULL_RESPONSE)
        + pubkey(0)
        + u64(2)
        + make_crds_value(0, pubkey(80))
        + make_crds_value(1, pubkey(81)),
    )
)
test_vectors.append(
    ("pullresp_huge_vec_len", u32(VARIANT_PULL_RESPONSE) + pubkey(0) + u64(999999999))
)

# -- PushMessage (variant 2) --
test_vectors.append(("push_empty_vec", u32(VARIANT_PUSH_MESSAGE) + pubkey(5) + u64(0)))
test_vectors.append(
    (
        "push_one_value",
        u32(VARIANT_PUSH_MESSAGE)
        + pubkey(5)
        + u64(1)
        + make_crds_value(11, pubkey(90)),
    )
)
test_vectors.append(
    ("push_truncated", u32(VARIANT_PUSH_MESSAGE) + pubkey(5) + u64(1) + signature(0))
)

# -- PullRequest (variant 0) --
test_vectors.append(
    (
        "pullreq_minimal_bloom",
        u32(VARIANT_PULL_REQUEST)
        + make_crds_filter(mask=0, mask_bits=0, bloom_keys=0, bloom_blocks=0)
        + make_crds_value(0, pubkey(70)),
    )
)
test_vectors.append(
    (
        "pullreq_standard_bloom",
        u32(VARIANT_PULL_REQUEST)
        + make_crds_filter(mask=0xDEAD, mask_bits=16, bloom_keys=3, bloom_blocks=2)
        + make_crds_value(0, pubkey(70)),
    )
)
test_vectors.append(
    (
        "pullreq_large_bloom",
        u32(VARIANT_PULL_REQUEST)
        + make_crds_filter(mask=0xFFFF, mask_bits=32, bloom_keys=5, bloom_blocks=4)
        + make_crds_value(11, pubkey(71)),
    )
)
test_vectors.append(
    (
        "pullreq_truncated_no_value",
        u32(VARIANT_PULL_REQUEST)
        + make_crds_filter(mask=0, mask_bits=0, bloom_keys=1, bloom_blocks=1),
    )
)

# -- CrdsData variant coverage --
for crds_variant in range(14):
    test_vectors.append(
        (
            f"push_crds_variant_{crds_variant}",
            u32(VARIANT_PUSH_MESSAGE)
            + pubkey(0)
            + u64(1)
            + make_crds_value(crds_variant, bytes(64)),
        )
    )


# ---- Generate .gossipctx files ----

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Generating {len(test_vectors)} gossip test vectors...")

for name, raw_bytes in test_vectors:
    msg = gossip_pb.GossipMessageBinary()
    msg.data = raw_bytes

    serialized = msg.SerializeToString(deterministic=True)
    content_hash = hashlib.sha3_256(serialized).hexdigest()[:16]
    filename = f"{name}_{content_hash}.gossipctx"

    with open(os.path.join(OUTPUT_DIR, filename), "wb") as f:
        f.write(serialized)

print(f"Wrote {len(test_vectors)} files to {OUTPUT_DIR}")
print("done!")
