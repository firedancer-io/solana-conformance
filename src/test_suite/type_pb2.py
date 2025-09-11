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
    name="type.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\ntype.proto\x12\x16org.solana.sealevel.v1\x1a\x0emetadata.proto"0\n\x0bTypeContext\x12\x0f\n\x07content\x18\x01 \x01(\x0c\x12\x10\n\x08typename\x18\x02 \x01(\t"C\n\x0bTypeEffects\x12\x0e\n\x06result\x18\x01 \x01(\x04\x12\x16\n\x0erepresentation\x18\x02 \x01(\x0c\x12\x0c\n\x04yaml\x18\x03 \x01(\x0c"±\x01\n\x0bTypeFixture\x129\n\x08metadata\x18\x01 \x01(\x0b2\'.org.solana.sealevel.v1.FixtureMetadata\x122\n\x05input\x18\x02 \x01(\x0b2#.org.solana.sealevel.v1.TypeContext\x123\n\x06output\x18\x03 \x01(\x0b2#.org.solana.sealevel.v1.TypeEffectsb\x06proto3'
    ),
    dependencies=[metadata__pb2.DESCRIPTOR],
)
_TYPECONTEXT = _descriptor.Descriptor(
    name="TypeContext",
    full_name="org.solana.sealevel.v1.TypeContext",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="content",
            full_name="org.solana.sealevel.v1.TypeContext.content",
            index=0,
            number=1,
            type=12,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b(""),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="typename",
            full_name="org.solana.sealevel.v1.TypeContext.typename",
            index=1,
            number=2,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b("").decode("utf-8"),
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
    serialized_start=54,
    serialized_end=102,
)
_TYPEEFFECTS = _descriptor.Descriptor(
    name="TypeEffects",
    full_name="org.solana.sealevel.v1.TypeEffects",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="result",
            full_name="org.solana.sealevel.v1.TypeEffects.result",
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
            name="representation",
            full_name="org.solana.sealevel.v1.TypeEffects.representation",
            index=1,
            number=2,
            type=12,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b(""),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="yaml",
            full_name="org.solana.sealevel.v1.TypeEffects.yaml",
            index=2,
            number=3,
            type=12,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=_b(""),
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
    serialized_end=171,
)
_TYPEFIXTURE = _descriptor.Descriptor(
    name="TypeFixture",
    full_name="org.solana.sealevel.v1.TypeFixture",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="metadata",
            full_name="org.solana.sealevel.v1.TypeFixture.metadata",
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
            full_name="org.solana.sealevel.v1.TypeFixture.input",
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
            full_name="org.solana.sealevel.v1.TypeFixture.output",
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
    serialized_start=174,
    serialized_end=351,
)
_TYPEFIXTURE.fields_by_name["metadata"].message_type = metadata__pb2._FIXTUREMETADATA
_TYPEFIXTURE.fields_by_name["input"].message_type = _TYPECONTEXT
_TYPEFIXTURE.fields_by_name["output"].message_type = _TYPEEFFECTS
DESCRIPTOR.message_types_by_name["TypeContext"] = _TYPECONTEXT
DESCRIPTOR.message_types_by_name["TypeEffects"] = _TYPEEFFECTS
DESCRIPTOR.message_types_by_name["TypeFixture"] = _TYPEFIXTURE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
TypeContext = _reflection.GeneratedProtocolMessageType(
    "TypeContext",
    (_message.Message,),
    dict(DESCRIPTOR=_TYPECONTEXT, __module__="type_pb2"),
)
_sym_db.RegisterMessage(TypeContext)
TypeEffects = _reflection.GeneratedProtocolMessageType(
    "TypeEffects",
    (_message.Message,),
    dict(DESCRIPTOR=_TYPEEFFECTS, __module__="type_pb2"),
)
_sym_db.RegisterMessage(TypeEffects)
TypeFixture = _reflection.GeneratedProtocolMessageType(
    "TypeFixture",
    (_message.Message,),
    dict(DESCRIPTOR=_TYPEFIXTURE, __module__="type_pb2"),
)
_sym_db.RegisterMessage(TypeFixture)
