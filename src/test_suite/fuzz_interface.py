from typing import Callable, Type, TypeVar
from google.protobuf import message, descriptor, message_factory
from dataclasses import dataclass, InitVar, field
import re

msg_factory = message_factory.MessageFactory()

FixtureType = TypeVar("FixtureType", bound=message.Message)
ContextType = TypeVar("ContextType", bound=message.Message)
EffectsType = TypeVar("EffectsType", bound=message.Message)

"""
Each fuzzing harness should implement this interface in fuzz_context.py

The following defines the interface:
- fuzz_fn_name: The name of the harness function to call in the fuzz target
- fixture_desc: The protobuf descriptor for the fixture message.
    - A fixture message is a message that contains an input and output message.
    - input: The fuzz target Context
    - output: The fuzz target Effects
- diff_effect_fn: A function that compares two effects messages for equality
- consensus_diff_effect_fn: Similar to above, but defines a diff function for consensus mode
- prune_effects_fn: A function that prunes effects to remove extra fields (e.g. remove accounts that weren't actually modified)
- human encode/decode functions for the context and effects messages to
  convert the messages to/from human-readable format (in-place).
  Both context and effects messages can have their own encode/decode functions.
"""


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


def generic_effects_prune(
    ctx: ContextType | None, effects: dict[str, str | None]
) -> dict[str, str | None] | None:
    if ctx is None:
        return None
    return effects


def generic_effects_diff(a: EffectsType, b: EffectsType) -> bool:
    return a == b


def generic_human_encode(obj: message.Message) -> None:
    pass


def generic_human_decode(obj: message.Message) -> None:
    pass


def generic_transform(obj: message.Message) -> None:
    """
    Allows for applying custom transformations to each fixture (mainly the context) before
    rerunning through the harness. For now, this is only used for fixture regeneration.
    As the user, you may modify `fixture` in-place before the fixture context gets run against
    a target and regenerated. To keep this function customizable, the implementation is left
    to the user to decide what they want to do with the data.
    """
    pass


@dataclass
class HarnessCtx:
    fuzz_fn_name: str
    fixture_desc: InitVar[descriptor.Descriptor]
    result_field_name: str | None = "result"
    diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = generic_effects_diff
    consensus_diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = (
        generic_effects_diff
    )
    core_bpf_diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = (
        generic_effects_diff
    )
    ignore_compute_units_diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = (
        generic_effects_diff
    )
    prune_effects_fn: Callable[
        [ContextType | None, dict[str, str | None]], dict[str, str | None] | None
    ] = generic_effects_prune
    context_human_encode_fn: Callable[[ContextType], None] = generic_human_encode
    context_human_decode_fn: Callable[[ContextType], None] = generic_human_decode
    effects_human_encode_fn: Callable[[EffectsType], None] = generic_human_encode
    effects_human_decode_fn: Callable[[EffectsType], None] = generic_human_decode
    regenerate_transformation_fn: Callable[[FixtureType], None] = generic_transform
    fixture_type: Type[FixtureType] = field(init=False)
    context_type: Type[ContextType] = field(init=False)
    effects_type: Type[EffectsType] = field(init=False)

    def __post_init__(self, fixture_desc):
        self.fixture_type = msg_factory.GetPrototype(fixture_desc)
        self.context_type = msg_factory.GetPrototype(
            fixture_desc.fields_by_name["input"].message_type
        )
        self.effects_type = msg_factory.GetPrototype(
            fixture_desc.fields_by_name["output"].message_type
        )

        effects_desc = fixture_desc.fields_by_name.get("output").message_type

        if effects_desc.fields_by_name.get(self.result_field_name) is None:
            self.result_field_name = None
