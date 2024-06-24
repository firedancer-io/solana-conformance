import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode("latin1"))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name="serialize.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\x0fserialize.proto\x12\x16org.solana.sealevel.v1"D\n\x0bVmMemRegion\x12\x0f\n\x07vm_addr\x18\x01 \x01(\x04\x12\x0f\n\x07content\x18\x02 \x01(\x0c\x12\x13\n\x0bis_writable\x18\x03 \x01(\x08"\\\n\x14InstrSerializeResult\x12\x0e\n\x06result\x18\x01 \x01(\x05\x124\n\x07regions\x18\x02 \x03(\x0b2#.org.solana.sealevel.v1.VmMemRegionb\x06proto3'
    ),
)
_VMMEMREGION = _descriptor.Descriptor(
    name="VmMemRegion",
    full_name="org.solana.sealevel.v1.VmMemRegion",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="vm_addr",
            full_name="org.solana.sealevel.v1.VmMemRegion.vm_addr",
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
            name="content",
            full_name="org.solana.sealevel.v1.VmMemRegion.content",
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
            name="is_writable",
            full_name="org.solana.sealevel.v1.VmMemRegion.is_writable",
            index=2,
            number=3,
            type=8,
            cpp_type=7,
            label=1,
            has_default_value=False,
            default_value=False,
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
    serialized_start=43,
    serialized_end=111,
)
_INSTRSERIALIZERESULT = _descriptor.Descriptor(
    name="InstrSerializeResult",
    full_name="org.solana.sealevel.v1.InstrSerializeResult",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="result",
            full_name="org.solana.sealevel.v1.InstrSerializeResult.result",
            index=0,
            number=1,
            type=5,
            cpp_type=1,
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
            name="regions",
            full_name="org.solana.sealevel.v1.InstrSerializeResult.regions",
            index=1,
            number=2,
            type=11,
            cpp_type=10,
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
    serialized_start=113,
    serialized_end=205,
)
_INSTRSERIALIZERESULT.fields_by_name["regions"].message_type = _VMMEMREGION
DESCRIPTOR.message_types_by_name["VmMemRegion"] = _VMMEMREGION
DESCRIPTOR.message_types_by_name["InstrSerializeResult"] = _INSTRSERIALIZERESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
VmMemRegion = _reflection.GeneratedProtocolMessageType(
    "VmMemRegion",
    (_message.Message,),
    dict(DESCRIPTOR=_VMMEMREGION, __module__="serialize_pb2"),
)
_sym_db.RegisterMessage(VmMemRegion)
InstrSerializeResult = _reflection.GeneratedProtocolMessageType(
    "InstrSerializeResult",
    (_message.Message,),
    dict(DESCRIPTOR=_INSTRSERIALIZERESULT, __module__="serialize_pb2"),
)
_sym_db.RegisterMessage(InstrSerializeResult)
