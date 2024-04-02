import base58
import superbased58
import os


def test_superbased58_32_bytes():
    """
    Tests superbased58 against base58 for 32 byte encoding/decoding.
    """
    for _ in range(10000):
        data = os.urandom(32)
        base_58_encoded = base58.b58encode(data)
        superbased58_encoded = superbased58.encode_32(data)
        assert base_58_encoded == superbased58_encoded
        assert base58.b58decode(base_58_encoded) == superbased58.decode_32(
            superbased58_encoded
        )


def test_superbased58_64_bytes():
    """
    Tests superbased58 against base58 for 64 byte encoding/decoding.
    """
    for _ in range(10000):
        data = os.urandom(64)
        base_58_encoded = base58.b58encode(data)
        superbased58_encoded = superbased58.encode_64(data)
        assert base_58_encoded == superbased58_encoded
        assert base58.b58decode(base_58_encoded) == superbased58.decode_64(
            superbased58_encoded
        )
