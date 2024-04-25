# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: invoke.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='invoke.proto',
  package='org.solana.sealevel.v1',
  syntax='proto3',
  serialized_pb=_b('\n\x0cinvoke.proto\x12\x16org.solana.sealevel.v1\"\x1e\n\nFeatureSet\x12\x10\n\x08\x66\x65\x61tures\x18\x01 \x03(\x06\"s\n\tAcctState\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\x0c\x12\x10\n\x08lamports\x18\x02 \x01(\x04\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\x0c\x12\x12\n\nexecutable\x18\x04 \x01(\x08\x12\x12\n\nrent_epoch\x18\x05 \x01(\x04\x12\r\n\x05owner\x18\x06 \x01(\x0c\"D\n\x0c\x45pochContext\x12\x34\n\x08\x66\x65\x61tures\x18\x01 \x01(\x0b\x32\".org.solana.sealevel.v1.FeatureSet\"\r\n\x0bSlotContext\"\x0c\n\nTxnContext\"B\n\tInstrAcct\x12\r\n\x05index\x18\x01 \x01(\r\x12\x13\n\x0bis_writable\x18\x02 \x01(\x08\x12\x11\n\tis_signer\x18\x03 \x01(\x08\"\xf6\x02\n\x0cInstrContext\x12\x12\n\nprogram_id\x18\x01 \x01(\x0c\x12\x11\n\tloader_id\x18\x02 \x01(\x0c\x12\x33\n\x08\x61\x63\x63ounts\x18\x03 \x03(\x0b\x32!.org.solana.sealevel.v1.AcctState\x12\x39\n\x0einstr_accounts\x18\x04 \x03(\x0b\x32!.org.solana.sealevel.v1.InstrAcct\x12\x0c\n\x04\x64\x61ta\x18\x05 \x01(\x0c\x12\x10\n\x08\x63u_avail\x18\x06 \x01(\x04\x12\x37\n\x0btxn_context\x18\x07 \x01(\x0b\x32\".org.solana.sealevel.v1.TxnContext\x12\x39\n\x0cslot_context\x18\x08 \x01(\x0b\x32#.org.solana.sealevel.v1.SlotContext\x12;\n\repoch_context\x18\t \x01(\x0b\x32$.org.solana.sealevel.v1.EpochContext\"\x97\x01\n\x0cInstrEffects\x12\x0e\n\x06result\x18\x01 \x01(\x05\x12\x12\n\ncustom_err\x18\x02 \x01(\r\x12<\n\x11modified_accounts\x18\x03 \x03(\x0b\x32!.org.solana.sealevel.v1.AcctState\x12\x10\n\x08\x63u_avail\x18\x04 \x01(\x04\x12\x13\n\x0breturn_data\x18\x05 \x01(\x0c\"y\n\x0cInstrFixture\x12\x33\n\x05input\x18\x01 \x01(\x0b\x32$.org.solana.sealevel.v1.InstrContext\x12\x34\n\x06output\x18\x02 \x01(\x0b\x32$.org.solana.sealevel.v1.InstrEffectsb\x06proto3')
)




_FEATURESET = _descriptor.Descriptor(
  name='FeatureSet',
  full_name='org.solana.sealevel.v1.FeatureSet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='features', full_name='org.solana.sealevel.v1.FeatureSet.features', index=0,
      number=1, type=6, cpp_type=4, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=40,
  serialized_end=70,
)


_ACCTSTATE = _descriptor.Descriptor(
  name='AcctState',
  full_name='org.solana.sealevel.v1.AcctState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='address', full_name='org.solana.sealevel.v1.AcctState.address', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lamports', full_name='org.solana.sealevel.v1.AcctState.lamports', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='data', full_name='org.solana.sealevel.v1.AcctState.data', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='executable', full_name='org.solana.sealevel.v1.AcctState.executable', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rent_epoch', full_name='org.solana.sealevel.v1.AcctState.rent_epoch', index=4,
      number=5, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='owner', full_name='org.solana.sealevel.v1.AcctState.owner', index=5,
      number=6, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=72,
  serialized_end=187,
)


_EPOCHCONTEXT = _descriptor.Descriptor(
  name='EpochContext',
  full_name='org.solana.sealevel.v1.EpochContext',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='features', full_name='org.solana.sealevel.v1.EpochContext.features', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=189,
  serialized_end=257,
)


_SLOTCONTEXT = _descriptor.Descriptor(
  name='SlotContext',
  full_name='org.solana.sealevel.v1.SlotContext',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=259,
  serialized_end=272,
)


_TXNCONTEXT = _descriptor.Descriptor(
  name='TxnContext',
  full_name='org.solana.sealevel.v1.TxnContext',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=274,
  serialized_end=286,
)


_INSTRACCT = _descriptor.Descriptor(
  name='InstrAcct',
  full_name='org.solana.sealevel.v1.InstrAcct',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='index', full_name='org.solana.sealevel.v1.InstrAcct.index', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_writable', full_name='org.solana.sealevel.v1.InstrAcct.is_writable', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_signer', full_name='org.solana.sealevel.v1.InstrAcct.is_signer', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=288,
  serialized_end=354,
)


_INSTRCONTEXT = _descriptor.Descriptor(
  name='InstrContext',
  full_name='org.solana.sealevel.v1.InstrContext',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='program_id', full_name='org.solana.sealevel.v1.InstrContext.program_id', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='loader_id', full_name='org.solana.sealevel.v1.InstrContext.loader_id', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='accounts', full_name='org.solana.sealevel.v1.InstrContext.accounts', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='instr_accounts', full_name='org.solana.sealevel.v1.InstrContext.instr_accounts', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='data', full_name='org.solana.sealevel.v1.InstrContext.data', index=4,
      number=5, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cu_avail', full_name='org.solana.sealevel.v1.InstrContext.cu_avail', index=5,
      number=6, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='txn_context', full_name='org.solana.sealevel.v1.InstrContext.txn_context', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='slot_context', full_name='org.solana.sealevel.v1.InstrContext.slot_context', index=7,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='epoch_context', full_name='org.solana.sealevel.v1.InstrContext.epoch_context', index=8,
      number=9, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=357,
  serialized_end=731,
)


_INSTREFFECTS = _descriptor.Descriptor(
  name='InstrEffects',
  full_name='org.solana.sealevel.v1.InstrEffects',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='result', full_name='org.solana.sealevel.v1.InstrEffects.result', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='custom_err', full_name='org.solana.sealevel.v1.InstrEffects.custom_err', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='modified_accounts', full_name='org.solana.sealevel.v1.InstrEffects.modified_accounts', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cu_avail', full_name='org.solana.sealevel.v1.InstrEffects.cu_avail', index=3,
      number=4, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='return_data', full_name='org.solana.sealevel.v1.InstrEffects.return_data', index=4,
      number=5, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=734,
  serialized_end=885,
)


_INSTRFIXTURE = _descriptor.Descriptor(
  name='InstrFixture',
  full_name='org.solana.sealevel.v1.InstrFixture',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='input', full_name='org.solana.sealevel.v1.InstrFixture.input', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='output', full_name='org.solana.sealevel.v1.InstrFixture.output', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=887,
  serialized_end=1008,
)

_EPOCHCONTEXT.fields_by_name['features'].message_type = _FEATURESET
_INSTRCONTEXT.fields_by_name['accounts'].message_type = _ACCTSTATE
_INSTRCONTEXT.fields_by_name['instr_accounts'].message_type = _INSTRACCT
_INSTRCONTEXT.fields_by_name['txn_context'].message_type = _TXNCONTEXT
_INSTRCONTEXT.fields_by_name['slot_context'].message_type = _SLOTCONTEXT
_INSTRCONTEXT.fields_by_name['epoch_context'].message_type = _EPOCHCONTEXT
_INSTREFFECTS.fields_by_name['modified_accounts'].message_type = _ACCTSTATE
_INSTRFIXTURE.fields_by_name['input'].message_type = _INSTRCONTEXT
_INSTRFIXTURE.fields_by_name['output'].message_type = _INSTREFFECTS
DESCRIPTOR.message_types_by_name['FeatureSet'] = _FEATURESET
DESCRIPTOR.message_types_by_name['AcctState'] = _ACCTSTATE
DESCRIPTOR.message_types_by_name['EpochContext'] = _EPOCHCONTEXT
DESCRIPTOR.message_types_by_name['SlotContext'] = _SLOTCONTEXT
DESCRIPTOR.message_types_by_name['TxnContext'] = _TXNCONTEXT
DESCRIPTOR.message_types_by_name['InstrAcct'] = _INSTRACCT
DESCRIPTOR.message_types_by_name['InstrContext'] = _INSTRCONTEXT
DESCRIPTOR.message_types_by_name['InstrEffects'] = _INSTREFFECTS
DESCRIPTOR.message_types_by_name['InstrFixture'] = _INSTRFIXTURE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FeatureSet = _reflection.GeneratedProtocolMessageType('FeatureSet', (_message.Message,), dict(
  DESCRIPTOR = _FEATURESET,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.FeatureSet)
  ))
_sym_db.RegisterMessage(FeatureSet)

AcctState = _reflection.GeneratedProtocolMessageType('AcctState', (_message.Message,), dict(
  DESCRIPTOR = _ACCTSTATE,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.AcctState)
  ))
_sym_db.RegisterMessage(AcctState)

EpochContext = _reflection.GeneratedProtocolMessageType('EpochContext', (_message.Message,), dict(
  DESCRIPTOR = _EPOCHCONTEXT,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.EpochContext)
  ))
_sym_db.RegisterMessage(EpochContext)

SlotContext = _reflection.GeneratedProtocolMessageType('SlotContext', (_message.Message,), dict(
  DESCRIPTOR = _SLOTCONTEXT,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.SlotContext)
  ))
_sym_db.RegisterMessage(SlotContext)

TxnContext = _reflection.GeneratedProtocolMessageType('TxnContext', (_message.Message,), dict(
  DESCRIPTOR = _TXNCONTEXT,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.TxnContext)
  ))
_sym_db.RegisterMessage(TxnContext)

InstrAcct = _reflection.GeneratedProtocolMessageType('InstrAcct', (_message.Message,), dict(
  DESCRIPTOR = _INSTRACCT,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.InstrAcct)
  ))
_sym_db.RegisterMessage(InstrAcct)

InstrContext = _reflection.GeneratedProtocolMessageType('InstrContext', (_message.Message,), dict(
  DESCRIPTOR = _INSTRCONTEXT,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.InstrContext)
  ))
_sym_db.RegisterMessage(InstrContext)

InstrEffects = _reflection.GeneratedProtocolMessageType('InstrEffects', (_message.Message,), dict(
  DESCRIPTOR = _INSTREFFECTS,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.InstrEffects)
  ))
_sym_db.RegisterMessage(InstrEffects)

InstrFixture = _reflection.GeneratedProtocolMessageType('InstrFixture', (_message.Message,), dict(
  DESCRIPTOR = _INSTRFIXTURE,
  __module__ = 'invoke_pb2'
  # @@protoc_insertion_point(class_scope:org.solana.sealevel.v1.InstrFixture)
  ))
_sym_db.RegisterMessage(InstrFixture)


# @@protoc_insertion_point(module_scope)
