import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode("latin1"))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

_sym_db = _symbol_database.Default()
from . import metadata_pb2 as metadata__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name="pack.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\npack.proto\x12\x16org.solana.sealevel.v1\x1a\x0emetadata.proto"/\n\x18PackComputeBudgetContext\x12\x13\n\x0binstr_datas\x18\x01 \x03(\x0c"\x87\x01\n\x18PackComputeBudgetEffects\x12\x1a\n\x12compute_unit_limit\x18\x01 \x01(\x04\x12\x0f\n\x07rewards\x18\x02 \x01(\x04\x12\x0f\n\x07heap_sz\x18\x03 \x01(\r\x12\x1b\n\x13loaded_acct_data_sz\x18\x04 \x01(\r\x12\x10\n\x08is_empty\x18\x05 \x01(\r"Ø\x01\n\x18PackComputeBudgetFixture\x129\n\x08metadata\x18\x01 \x01(\x0b2\'.org.solana.sealevel.v1.FixtureMetadata\x12?\n\x05input\x18\x02 \x01(\x0b20.org.solana.sealevel.v1.PackComputeBudgetContext\x12@\n\x06output\x18\x03 \x01(\x0b20.org.solana.sealevel.v1.PackComputeBudgetEffectsb\x06proto3'
    ),
    dependencies=[metadata__pb2.DESCRIPTOR],
)
_PACKCOMPUTEBUDGETCONTEXT = _descriptor.Descriptor(
    name="PackComputeBudgetContext",
    full_name="org.solana.sealevel.v1.PackComputeBudgetContext",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="instr_datas",
            full_name="org.solana.sealevel.v1.PackComputeBudgetContext.instr_datas",
            index=0,
            number=1,
            type=12,
            cpp_type=9,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        )
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=54,
    serialized_end=101,
)
_PACKCOMPUTEBUDGETEFFECTS = _descriptor.Descriptor(
    name="PackComputeBudgetEffects",
    full_name="org.solana.sealevel.v1.PackComputeBudgetEffects",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="compute_unit_limit",
            full_name="org.solana.sealevel.v1.PackComputeBudgetEffects.compute_unit_limit",
            index=0,
            number=1,
            type=4,
            cpp_type=4,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="rewards",
            full_name="org.solana.sealevel.v1.PackComputeBudgetEffects.rewards",
            index=1,
            number=2,
            type=4,
            cpp_type=4,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="heap_sz",
            full_name="org.solana.sealevel.v1.PackComputeBudgetEffects.heap_sz",
            index=2,
            number=3,
            type=13,
            cpp_type=3,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="loaded_acct_data_sz",
            full_name="org.solana.sealevel.v1.PackComputeBudgetEffects.loaded_acct_data_sz",
            index=3,
            number=4,
            type=13,
            cpp_type=3,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="is_empty",
            full_name="org.solana.sealevel.v1.PackComputeBudgetEffects.is_empty",
            index=4,
            number=5,
            type=13,
            cpp_type=3,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=104,
    serialized_end=239,
)
_PACKCOMPUTEBUDGETFIXTURE = _descriptor.Descriptor(
    name="PackComputeBudgetFixture",
    full_name="org.solana.sealevel.v1.PackComputeBudgetFixture",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="metadata",
            full_name="org.solana.sealevel.v1.PackComputeBudgetFixture.metadata",
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="input",
            full_name="org.solana.sealevel.v1.PackComputeBudgetFixture.input",
            index=1,
            number=2,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="output",
            full_name="org.solana.sealevel.v1.PackComputeBudgetFixture.output",
            index=2,
            number=3,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=242,
    serialized_end=458,
)
_PACKCOMPUTEBUDGETFIXTURE.fields_by_name["metadata"].message_type = (
    metadata__pb2._FIXTUREMETADATA
)
_PACKCOMPUTEBUDGETFIXTURE.fields_by_name["input"].message_type = (
    _PACKCOMPUTEBUDGETCONTEXT
)
_PACKCOMPUTEBUDGETFIXTURE.fields_by_name["output"].message_type = (
    _PACKCOMPUTEBUDGETEFFECTS
)
DESCRIPTOR.message_types_by_name["PackComputeBudgetContext"] = _PACKCOMPUTEBUDGETCONTEXT
DESCRIPTOR.message_types_by_name["PackComputeBudgetEffects"] = _PACKCOMPUTEBUDGETEFFECTS
DESCRIPTOR.message_types_by_name["PackComputeBudgetFixture"] = _PACKCOMPUTEBUDGETFIXTURE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
PackComputeBudgetContext = _reflection.GeneratedProtocolMessageType(
    "PackComputeBudgetContext",
    (_message.Message,),
    dict(DESCRIPTOR=_PACKCOMPUTEBUDGETCONTEXT, __module__="pack_pb2"),
)
_sym_db.RegisterMessage(PackComputeBudgetContext)
PackComputeBudgetEffects = _reflection.GeneratedProtocolMessageType(
    "PackComputeBudgetEffects",
    (_message.Message,),
    dict(DESCRIPTOR=_PACKCOMPUTEBUDGETEFFECTS, __module__="pack_pb2"),
)
_sym_db.RegisterMessage(PackComputeBudgetEffects)
PackComputeBudgetFixture = _reflection.GeneratedProtocolMessageType(
    "PackComputeBudgetFixture",
    (_message.Message,),
    dict(DESCRIPTOR=_PACKCOMPUTEBUDGETFIXTURE, __module__="pack_pb2"),
)
_sym_db.RegisterMessage(PackComputeBudgetFixture)
