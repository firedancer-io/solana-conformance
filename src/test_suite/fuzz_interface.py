from typing import Callable, Type, TypeVar
from google.protobuf import message, descriptor, message_factory
from dataclasses import dataclass, InitVar, field

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
- human encode/decode functions for the context and effects messages to
  convert the messages to/from human-readable format (in-place).
  Both context and effects messages can have their own encode/decode functions.
"""


def generic_effects_diff(a: EffectsType, b: EffectsType) -> bool:
    return a == b


def generic_human_encode(obj: message.Message) -> None:
    pass


def generic_human_decode(obj: message.Message) -> None:
    pass


@dataclass
class HarnessCtx:
    fuzz_fn_name: str
    fixture_desc: InitVar[descriptor.Descriptor]
    result_field_name: str | None = "result"
    diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = generic_effects_diff
    context_human_encode_fn: Callable[[ContextType], None] = generic_human_encode
    context_human_decode_fn: Callable[[ContextType], None] = generic_human_decode
    effects_human_encode_fn: Callable[[EffectsType], None] = generic_human_encode
    effects_human_decode_fn: Callable[[EffectsType], None] = generic_human_decode
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
