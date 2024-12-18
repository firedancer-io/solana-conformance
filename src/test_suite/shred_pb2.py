import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode("latin1"))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name="shred.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\x0bshred.proto\x12\x16org.solana.sealevel.v1"\x1b\n\x0bShredBinary\x12\x0c\n\x04data\x18\x01 \x01(\x0c"=\n\nDataHeader\x12\x12\n\nparent_off\x18\x01 \x01(\r\x12\r\n\x05flags\x18\x02 \x01(\r\x12\x0c\n\x04size\x18\x03 \x01(\r"=\n\nCodeHeader\x12\x10\n\x08data_cnt\x18\x01 \x01(\r\x12\x10\n\x08code_cnt\x18\x02 \x01(\r\x12\x0b\n\x03idx\x18\x03 \x01(\r"è\x01\n\x0bParsedShred\x12\x11\n\tsignature\x18\x01 \x01(\t\x12\x0f\n\x07variant\x18\x02 \x01(\r\x12\x0c\n\x04slot\x18\x03 \x01(\x04\x12\x0b\n\x03idx\x18\x04 \x01(\r\x12\x0f\n\x07version\x18\x05 \x01(\r\x12\x13\n\x0bfec_set_idx\x18\x06 \x01(\r\x122\n\x04data\x18\x07 \x01(\x0b2".org.solana.sealevel.v1.DataHeaderH\x00\x122\n\x04code\x18\x08 \x01(\x0b2".org.solana.sealevel.v1.CodeHeaderH\x00B\x0c\n\nshred_type"\x1d\n\x0cAcceptsShred\x12\r\n\x05valid\x18\x01 \x01(\x08b\x06proto3'
    ),
)
_SHREDBINARY = _descriptor.Descriptor(
    name="ShredBinary",
    full_name="org.solana.sealevel.v1.ShredBinary",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="data",
            full_name="org.solana.sealevel.v1.ShredBinary.data",
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
    serialized_start=39,
    serialized_end=66,
)
_DATAHEADER = _descriptor.Descriptor(
    name="DataHeader",
    full_name="org.solana.sealevel.v1.DataHeader",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="parent_off",
            full_name="org.solana.sealevel.v1.DataHeader.parent_off",
            index=0,
            number=1,
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
            name="flags",
            full_name="org.solana.sealevel.v1.DataHeader.flags",
            index=1,
            number=2,
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
            name="size",
            full_name="org.solana.sealevel.v1.DataHeader.size",
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
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=68,
    serialized_end=129,
)
_CODEHEADER = _descriptor.Descriptor(
    name="CodeHeader",
    full_name="org.solana.sealevel.v1.CodeHeader",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="data_cnt",
            full_name="org.solana.sealevel.v1.CodeHeader.data_cnt",
            index=0,
            number=1,
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
            name="code_cnt",
            full_name="org.solana.sealevel.v1.CodeHeader.code_cnt",
            index=1,
            number=2,
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
            name="idx",
            full_name="org.solana.sealevel.v1.CodeHeader.idx",
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
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=131,
    serialized_end=192,
)
_PARSEDSHRED = _descriptor.Descriptor(
    name="ParsedShred",
    full_name="org.solana.sealevel.v1.ParsedShred",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="signature",
            full_name="org.solana.sealevel.v1.ParsedShred.signature",
            index=0,
            number=1,
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
        _descriptor.FieldDescriptor(
            name="variant",
            full_name="org.solana.sealevel.v1.ParsedShred.variant",
            index=1,
            number=2,
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
            name="slot",
            full_name="org.solana.sealevel.v1.ParsedShred.slot",
            index=2,
            number=3,
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
            name="idx",
            full_name="org.solana.sealevel.v1.ParsedShred.idx",
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
            name="version",
            full_name="org.solana.sealevel.v1.ParsedShred.version",
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
        _descriptor.FieldDescriptor(
            name="fec_set_idx",
            full_name="org.solana.sealevel.v1.ParsedShred.fec_set_idx",
            index=5,
            number=6,
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
            name="data",
            full_name="org.solana.sealevel.v1.ParsedShred.data",
            index=6,
            number=7,
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
            name="code",
            full_name="org.solana.sealevel.v1.ParsedShred.code",
            index=7,
            number=8,
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
    oneofs=[
        _descriptor.OneofDescriptor(
            name="shred_type",
            full_name="org.solana.sealevel.v1.ParsedShred.shred_type",
            index=0,
            containing_type=None,
            fields=[],
        )
    ],
    serialized_start=195,
    serialized_end=427,
)
_ACCEPTSSHRED = _descriptor.Descriptor(
    name="AcceptsShred",
    full_name="org.solana.sealevel.v1.AcceptsShred",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="valid",
            full_name="org.solana.sealevel.v1.AcceptsShred.valid",
            index=0,
            number=1,
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
    serialized_start=429,
    serialized_end=458,
)
_PARSEDSHRED.fields_by_name["data"].message_type = _DATAHEADER
_PARSEDSHRED.fields_by_name["code"].message_type = _CODEHEADER
_PARSEDSHRED.oneofs_by_name["shred_type"].fields.append(
    _PARSEDSHRED.fields_by_name["data"]
)
_PARSEDSHRED.fields_by_name["data"].containing_oneof = _PARSEDSHRED.oneofs_by_name[
    "shred_type"
]
_PARSEDSHRED.oneofs_by_name["shred_type"].fields.append(
    _PARSEDSHRED.fields_by_name["code"]
)
_PARSEDSHRED.fields_by_name["code"].containing_oneof = _PARSEDSHRED.oneofs_by_name[
    "shred_type"
]
DESCRIPTOR.message_types_by_name["ShredBinary"] = _SHREDBINARY
DESCRIPTOR.message_types_by_name["DataHeader"] = _DATAHEADER
DESCRIPTOR.message_types_by_name["CodeHeader"] = _CODEHEADER
DESCRIPTOR.message_types_by_name["ParsedShred"] = _PARSEDSHRED
DESCRIPTOR.message_types_by_name["AcceptsShred"] = _ACCEPTSSHRED
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
ShredBinary = _reflection.GeneratedProtocolMessageType(
    "ShredBinary",
    (_message.Message,),
    dict(DESCRIPTOR=_SHREDBINARY, __module__="shred_pb2"),
)
_sym_db.RegisterMessage(ShredBinary)
DataHeader = _reflection.GeneratedProtocolMessageType(
    "DataHeader",
    (_message.Message,),
    dict(DESCRIPTOR=_DATAHEADER, __module__="shred_pb2"),
)
_sym_db.RegisterMessage(DataHeader)
CodeHeader = _reflection.GeneratedProtocolMessageType(
    "CodeHeader",
    (_message.Message,),
    dict(DESCRIPTOR=_CODEHEADER, __module__="shred_pb2"),
)
_sym_db.RegisterMessage(CodeHeader)
ParsedShred = _reflection.GeneratedProtocolMessageType(
    "ParsedShred",
    (_message.Message,),
    dict(DESCRIPTOR=_PARSEDSHRED, __module__="shred_pb2"),
)
_sym_db.RegisterMessage(ParsedShred)
AcceptsShred = _reflection.GeneratedProtocolMessageType(
    "AcceptsShred",
    (_message.Message,),
    dict(DESCRIPTOR=_ACCEPTSSHRED, __module__="shred_pb2"),
)
_sym_db.RegisterMessage(AcceptsShred)
