import fd58
from test_suite.context.codec_utils import (
    decode_acct_state,
    decode_hex_compact,
    encode_acct_state,
    encode_hex_compact,
)
import test_suite.elf_pb2 as elf_pb


def decode_input(elf_context: elf_pb.ELFLoaderCtx):
    """
    Decode ELFLoaderContext fields in-place into human-readable format.
    Addresses are decoded from base58, data from base64.

    Args:
        - elf_context (elf_pb.ELFLoaderContext): Loader context (will be modified).
    """
    # ELF data
    if elf_context.elf.data:
        elf_context.elf.data = decode_hex_compact(elf_context.elf.data)


def encode_input(elf_context: elf_pb.ELFLoaderCtx):
    """
    Encode ELFLoaderContext fields in-place into binary, digestable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - elf_context (elf_pb.ELFLoaderContext): Loader context (will be modified).
    """
    # ELF data
    if elf_context.elf.data:
        elf_context.elf.data = encode_hex_compact(elf_context.elf.data)


def encode_output(elf_effects: elf_pb.ELFLoaderEffects):
    """
    Encode ELFLoaderEffects fields in-place into human-readable format.
    Addresses are encoded in base58, data in base64.

    Args:
        - elf_effects (elf_pb.ELFLoaderEffects): Loader effects (will be modified).
    """
    # Rodata
    if elf_effects.rodata:
        elf_effects.rodata = encode_hex_compact(elf_effects.rodata)
