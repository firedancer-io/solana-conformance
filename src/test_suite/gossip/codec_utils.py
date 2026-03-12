import test_suite.protos.gossip_pb2 as gossip_pb

VARIANT_NAMES = {
    0: "PullRequest",
    1: "PullResponse",
    2: "PushMessage",
    3: "PruneMessage",
    4: "PingMessage",
    5: "PongMessage",
}


def encode_input(msg: gossip_pb.GossipMessageBinary):
    """Encode GossipMessageBinary fields in-place into human-readable hex."""
    if msg.data:
        raw = msg.data
        variant = int.from_bytes(raw[:4], "little") if len(raw) >= 4 else None
        variant_name = VARIANT_NAMES.get(variant, f"Unknown({variant})")
        msg.data = f"[{variant_name}] {raw.hex()}".encode("ascii")


def decode_input(msg: gossip_pb.GossipMessageBinary):
    """Decode human-readable hex back into raw bytes."""
    if msg.data:
        text = msg.data.decode("ascii")
        if text.startswith("["):
            _, hex_str = text.split("] ", 1)
        else:
            hex_str = text
        msg.data = bytes.fromhex(hex_str)


def encode_output(effects: gossip_pb.AcceptsGossipMessage):
    """No-op: output is just a bool, already human-readable."""
    pass
