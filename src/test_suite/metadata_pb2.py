"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name="metadata.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
    serialized_pb=b'\n\x0emetadata.proto\x12\x16org.solana.sealevel.v1"(\n\x0fFixtureMetadata\x12\x15\n\rfn_entrypoint\x18\x01 \x01(\tb\x06proto3',
)
_FIXTUREMETADATA = _descriptor.Descriptor(
    name="FixtureMetadata",
    full_name="org.solana.sealevel.v1.FixtureMetadata",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name="fn_entrypoint",
            full_name="org.solana.sealevel.v1.FixtureMetadata.fn_entrypoint",
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
            create_key=_descriptor._internal_create_key,
        )
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=42,
    serialized_end=82,
)
DESCRIPTOR.message_types_by_name["FixtureMetadata"] = _FIXTUREMETADATA
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
FixtureMetadata = _reflection.GeneratedProtocolMessageType(
    "FixtureMetadata",
    (_message.Message,),
    {"DESCRIPTOR": _FIXTUREMETADATA, "__module__": "metadata_pb2"},
)
_sym_db.RegisterMessage(FixtureMetadata)
