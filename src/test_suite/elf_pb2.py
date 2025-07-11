import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode("latin1"))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

_sym_db = _symbol_database.Default()
from . import context_pb2 as context__pb2
from . import metadata_pb2 as metadata__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name="elf.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\telf.proto\x12\x16org.solana.sealevel.v1\x1a\rcontext.proto\x1a\x0emetadata.proto"\x19\n\tELFBinary\x12\x0c\n\x04data\x18\x01 \x01(\x0c"\x8b\x01\n\x0cELFLoaderCtx\x12.\n\x03elf\x18\x01 \x01(\x0b2!.org.solana.sealevel.v1.ELFBinary\x124\n\x08features\x18\x02 \x01(\x0b2".org.solana.sealevel.v1.FeatureSet\x12\x15\n\rdeploy_checks\x18\x04 \x01(\x08"~\n\x10ELFLoaderEffects\x12\x0e\n\x06rodata\x18\x01 \x01(\x0c\x12\x11\n\trodata_sz\x18\x02 \x01(\x04\x12\x10\n\x08text_cnt\x18\x04 \x01(\x04\x12\x10\n\x08text_off\x18\x05 \x01(\x04\x12\x10\n\x08entry_pc\x18\x06 \x01(\x04\x12\x11\n\tcalldests\x18\x07 \x03(\x04"¼\x01\n\x10ELFLoaderFixture\x129\n\x08metadata\x18\x01 \x01(\x0b2\'.org.solana.sealevel.v1.FixtureMetadata\x123\n\x05input\x18\x02 \x01(\x0b2$.org.solana.sealevel.v1.ELFLoaderCtx\x128\n\x06output\x18\x03 \x01(\x0b2(.org.solana.sealevel.v1.ELFLoaderEffectsb\x06proto3'
    ),
    dependencies=[context__pb2.DESCRIPTOR, metadata__pb2.DESCRIPTOR],
)
_ELFBINARY = _descriptor.Descriptor(
    name="ELFBinary",
    full_name="org.solana.sealevel.v1.ELFBinary",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="data",
            full_name="org.solana.sealevel.v1.ELFBinary.data",
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
    serialized_start=68,
    serialized_end=93,
)
_ELFLOADERCTX = _descriptor.Descriptor(
    name="ELFLoaderCtx",
    full_name="org.solana.sealevel.v1.ELFLoaderCtx",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="elf",
            full_name="org.solana.sealevel.v1.ELFLoaderCtx.elf",
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
            name="features",
            full_name="org.solana.sealevel.v1.ELFLoaderCtx.features",
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
            name="deploy_checks",
            full_name="org.solana.sealevel.v1.ELFLoaderCtx.deploy_checks",
            index=2,
            number=4,
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
    serialized_start=96,
    serialized_end=235,
)
_ELFLOADEREFFECTS = _descriptor.Descriptor(
    name="ELFLoaderEffects",
    full_name="org.solana.sealevel.v1.ELFLoaderEffects",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="rodata",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.rodata",
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
            name="rodata_sz",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.rodata_sz",
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
            name="text_cnt",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.text_cnt",
            index=2,
            number=4,
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
            name="text_off",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.text_off",
            index=3,
            number=5,
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
            name="entry_pc",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.entry_pc",
            index=4,
            number=6,
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
            name="calldests",
            full_name="org.solana.sealevel.v1.ELFLoaderEffects.calldests",
            index=5,
            number=7,
            type=4,
            cpp_type=4,
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
    serialized_start=237,
    serialized_end=363,
)
_ELFLOADERFIXTURE = _descriptor.Descriptor(
    name="ELFLoaderFixture",
    full_name="org.solana.sealevel.v1.ELFLoaderFixture",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="metadata",
            full_name="org.solana.sealevel.v1.ELFLoaderFixture.metadata",
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
            full_name="org.solana.sealevel.v1.ELFLoaderFixture.input",
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
            full_name="org.solana.sealevel.v1.ELFLoaderFixture.output",
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
    serialized_start=366,
    serialized_end=554,
)
_ELFLOADERCTX.fields_by_name["elf"].message_type = _ELFBINARY
_ELFLOADERCTX.fields_by_name["features"].message_type = context__pb2._FEATURESET
_ELFLOADERFIXTURE.fields_by_name["metadata"].message_type = (
    metadata__pb2._FIXTUREMETADATA
)
_ELFLOADERFIXTURE.fields_by_name["input"].message_type = _ELFLOADERCTX
_ELFLOADERFIXTURE.fields_by_name["output"].message_type = _ELFLOADEREFFECTS
DESCRIPTOR.message_types_by_name["ELFBinary"] = _ELFBINARY
DESCRIPTOR.message_types_by_name["ELFLoaderCtx"] = _ELFLOADERCTX
DESCRIPTOR.message_types_by_name["ELFLoaderEffects"] = _ELFLOADEREFFECTS
DESCRIPTOR.message_types_by_name["ELFLoaderFixture"] = _ELFLOADERFIXTURE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
ELFBinary = _reflection.GeneratedProtocolMessageType(
    "ELFBinary", (_message.Message,), dict(DESCRIPTOR=_ELFBINARY, __module__="elf_pb2")
)
_sym_db.RegisterMessage(ELFBinary)
ELFLoaderCtx = _reflection.GeneratedProtocolMessageType(
    "ELFLoaderCtx",
    (_message.Message,),
    dict(DESCRIPTOR=_ELFLOADERCTX, __module__="elf_pb2"),
)
_sym_db.RegisterMessage(ELFLoaderCtx)
ELFLoaderEffects = _reflection.GeneratedProtocolMessageType(
    "ELFLoaderEffects",
    (_message.Message,),
    dict(DESCRIPTOR=_ELFLOADEREFFECTS, __module__="elf_pb2"),
)
_sym_db.RegisterMessage(ELFLoaderEffects)
ELFLoaderFixture = _reflection.GeneratedProtocolMessageType(
    "ELFLoaderFixture",
    (_message.Message,),
    dict(DESCRIPTOR=_ELFLOADERFIXTURE, __module__="elf_pb2"),
)
_sym_db.RegisterMessage(ELFLoaderFixture)
