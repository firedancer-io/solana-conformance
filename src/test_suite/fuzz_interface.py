from typing import Callable, Type, TypeVar
from google.protobuf import message, descriptor, message_factory
from dataclasses import dataclass, InitVar

msg_factory = message_factory.MessageFactory()

FixtureType = TypeVar("FixtureType", bound=message.Message)
ContextType = TypeVar("ContextType", bound=message.Message)
EffectsType = TypeVar("EffectsType", bound=message.Message)

"""
Each fuzzing harness should implement this interface.
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
    diff_effect_fn: Callable[[EffectsType, EffectsType], bool] = generic_effects_diff
    context_human_encode_fn: Callable[[ContextType], None] = generic_human_encode
    context_human_decode_fn: Callable[[ContextType], None] = generic_human_decode
    effects_human_encode_fn: Callable[[EffectsType], None] = generic_human_encode
    effects_human_decode_fn: Callable[[EffectsType], None] = generic_human_decode
    fixture_type: Type[FixtureType] = message.Message
    context_type: Type[ContextType] = message.Message
    effects_type: Type[EffectsType] = message.Message

    def __post_init__(self, fixture_desc):
        self.fixture_type = msg_factory.GetPrototype(fixture_desc)
        self.context_type = msg_factory.GetPrototype(
            fixture_desc.fields_by_name["input"].message_type
        )
        self.effects_type = msg_factory.GetPrototype(
            fixture_desc.fields_by_name["output"].message_type
        )
