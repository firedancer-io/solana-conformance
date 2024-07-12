import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode("latin1"))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

_sym_db = _symbol_database.Default()
from . import context_pb2 as context__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name="txn.proto",
    package="org.solana.sealevel.v1",
    syntax="proto3",
    serialized_pb=_b(
        '\n\ttxn.proto\x12\x16org.solana.sealevel.v1\x1a\rcontext.proto"~\n\rMessageHeader\x12\x1f\n\x17num_required_signatures\x18\x01 \x01(\r\x12$\n\x1cnum_readonly_signed_accounts\x18\x02 \x01(\r\x12&\n\x1enum_readonly_unsigned_accounts\x18\x03 \x01(\r"O\n\x13CompiledInstruction\x12\x18\n\x10program_id_index\x18\x01 \x01(\r\x12\x10\n\x08accounts\x18\x02 \x03(\r\x12\x0c\n\x04data\x18\x03 \x01(\x0c"d\n\x19MessageAddressTableLookup\x12\x13\n\x0baccount_key\x18\x01 \x01(\x0c\x12\x18\n\x10writable_indexes\x18\x02 \x03(\r\x12\x18\n\x10readonly_indexes\x18\x03 \x03(\r"5\n\x0fLoadedAddresses\x12\x10\n\x08writable\x18\x01 \x03(\x0c\x12\x10\n\x08readonly\x18\x02 \x03(\x0c"¦\x03\n\x12TransactionMessage\x12\x11\n\tis_legacy\x18\x01 \x01(\x08\x125\n\x06header\x18\x02 \x01(\x0b2%.org.solana.sealevel.v1.MessageHeader\x12\x14\n\x0caccount_keys\x18\x03 \x03(\x0c\x12>\n\x13account_shared_data\x18\x04 \x03(\x0b2!.org.solana.sealevel.v1.AcctState\x12\x18\n\x10recent_blockhash\x18\x05 \x01(\x0c\x12A\n\x0cinstructions\x18\x06 \x03(\x0b2+.org.solana.sealevel.v1.CompiledInstruction\x12P\n\x15address_table_lookups\x18\x07 \x03(\x0b21.org.solana.sealevel.v1.MessageAddressTableLookup\x12A\n\x10loaded_addresses\x18\x08 \x01(\x0b2\'.org.solana.sealevel.v1.LoadedAddresses"\x98\x01\n\x14SanitizedTransaction\x12;\n\x07message\x18\x01 \x01(\x0b2*.org.solana.sealevel.v1.TransactionMessage\x12\x14\n\x0cmessage_hash\x18\x02 \x01(\x0c\x12\x19\n\x11is_simple_vote_tx\x18\x03 \x01(\x08\x12\x12\n\nsignatures\x18\x04 \x03(\x0c"à\x01\n\nTxnContext\x128\n\x02tx\x18\x01 \x01(\x0b2,.org.solana.sealevel.v1.SanitizedTransaction\x12\x0f\n\x07max_age\x18\x02 \x01(\x04\x12\x17\n\x0fblockhash_queue\x18\x03 \x03(\x0c\x127\n\tepoch_ctx\x18\x04 \x01(\x0b2$.org.solana.sealevel.v1.EpochContext\x125\n\x08slot_ctx\x18\x05 \x01(\x0b2#.org.solana.sealevel.v1.SlotContext"\x9b\x01\n\x0eResultingState\x126\n\x0bacct_states\x18\x01 \x03(\x0b2!.org.solana.sealevel.v1.AcctState\x127\n\x0brent_debits\x18\x02 \x03(\x0b2".org.solana.sealevel.v1.RentDebits\x12\x18\n\x10transaction_rent\x18\x03 \x01(\x04"4\n\nRentDebits\x12\x0e\n\x06pubkey\x18\x01 \x01(\x0c\x12\x16\n\x0erent_collected\x18\x02 \x01(\x03"A\n\nFeeDetails\x12\x17\n\x0ftransaction_fee\x18\x01 \x01(\x04\x12\x1a\n\x12prioritization_fee\x18\x02 \x01(\x04"®\x02\n\tTxnResult\x12\x10\n\x08executed\x18\x01 \x01(\x08\x12\x1a\n\x12sanitization_error\x18\x02 \x01(\x08\x12?\n\x0fresulting_state\x18\x03 \x01(\x0b2&.org.solana.sealevel.v1.ResultingState\x12\x0c\n\x04rent\x18\x04 \x01(\x04\x12\r\n\x05is_ok\x18\x05 \x01(\x08\x12\x0e\n\x06status\x18\x06 \x01(\r\x12\x13\n\x0breturn_data\x18\x07 \x01(\x0c\x12\x16\n\x0eexecuted_units\x18\x08 \x01(\x04\x12\x1f\n\x17accounts_data_len_delta\x18\t \x01(\x03\x127\n\x0bfee_details\x18\n \x01(\x0b2".org.solana.sealevel.v1.FeeDetails"r\n\nTxnFixture\x121\n\x05input\x18\x01 \x01(\x0b2".org.solana.sealevel.v1.TxnContext\x121\n\x06output\x18\x02 \x01(\x0b2!.org.solana.sealevel.v1.TxnResultb\x06proto3'
    ),
    dependencies=[context__pb2.DESCRIPTOR],
)
_MESSAGEHEADER = _descriptor.Descriptor(
    name="MessageHeader",
    full_name="org.solana.sealevel.v1.MessageHeader",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="num_required_signatures",
            full_name="org.solana.sealevel.v1.MessageHeader.num_required_signatures",
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
            name="num_readonly_signed_accounts",
            full_name="org.solana.sealevel.v1.MessageHeader.num_readonly_signed_accounts",
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
            name="num_readonly_unsigned_accounts",
            full_name="org.solana.sealevel.v1.MessageHeader.num_readonly_unsigned_accounts",
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
    serialized_start=52,
    serialized_end=178,
)
_COMPILEDINSTRUCTION = _descriptor.Descriptor(
    name="CompiledInstruction",
    full_name="org.solana.sealevel.v1.CompiledInstruction",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="program_id_index",
            full_name="org.solana.sealevel.v1.CompiledInstruction.program_id_index",
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
            name="accounts",
            full_name="org.solana.sealevel.v1.CompiledInstruction.accounts",
            index=1,
            number=2,
            type=13,
            cpp_type=3,
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
        _descriptor.FieldDescriptor(
            name="data",
            full_name="org.solana.sealevel.v1.CompiledInstruction.data",
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
    serialized_start=180,
    serialized_end=259,
)
_MESSAGEADDRESSTABLELOOKUP = _descriptor.Descriptor(
    name="MessageAddressTableLookup",
    full_name="org.solana.sealevel.v1.MessageAddressTableLookup",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="account_key",
            full_name="org.solana.sealevel.v1.MessageAddressTableLookup.account_key",
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
            name="writable_indexes",
            full_name="org.solana.sealevel.v1.MessageAddressTableLookup.writable_indexes",
            index=1,
            number=2,
            type=13,
            cpp_type=3,
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
        _descriptor.FieldDescriptor(
            name="readonly_indexes",
            full_name="org.solana.sealevel.v1.MessageAddressTableLookup.readonly_indexes",
            index=2,
            number=3,
            type=13,
            cpp_type=3,
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
    serialized_start=261,
    serialized_end=361,
)
_LOADEDADDRESSES = _descriptor.Descriptor(
    name="LoadedAddresses",
    full_name="org.solana.sealevel.v1.LoadedAddresses",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="writable",
            full_name="org.solana.sealevel.v1.LoadedAddresses.writable",
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
        ),
        _descriptor.FieldDescriptor(
            name="readonly",
            full_name="org.solana.sealevel.v1.LoadedAddresses.readonly",
            index=1,
            number=2,
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
    serialized_start=363,
    serialized_end=416,
)
_TRANSACTIONMESSAGE = _descriptor.Descriptor(
    name="TransactionMessage",
    full_name="org.solana.sealevel.v1.TransactionMessage",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="is_legacy",
            full_name="org.solana.sealevel.v1.TransactionMessage.is_legacy",
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
        ),
        _descriptor.FieldDescriptor(
            name="header",
            full_name="org.solana.sealevel.v1.TransactionMessage.header",
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
            name="account_keys",
            full_name="org.solana.sealevel.v1.TransactionMessage.account_keys",
            index=2,
            number=3,
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
        ),
        _descriptor.FieldDescriptor(
            name="account_shared_data",
            full_name="org.solana.sealevel.v1.TransactionMessage.account_shared_data",
            index=3,
            number=4,
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
        _descriptor.FieldDescriptor(
            name="recent_blockhash",
            full_name="org.solana.sealevel.v1.TransactionMessage.recent_blockhash",
            index=4,
            number=5,
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
            name="instructions",
            full_name="org.solana.sealevel.v1.TransactionMessage.instructions",
            index=5,
            number=6,
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
        _descriptor.FieldDescriptor(
            name="address_table_lookups",
            full_name="org.solana.sealevel.v1.TransactionMessage.address_table_lookups",
            index=6,
            number=7,
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
        _descriptor.FieldDescriptor(
            name="loaded_addresses",
            full_name="org.solana.sealevel.v1.TransactionMessage.loaded_addresses",
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
    oneofs=[],
    serialized_start=419,
    serialized_end=841,
)
_SANITIZEDTRANSACTION = _descriptor.Descriptor(
    name="SanitizedTransaction",
    full_name="org.solana.sealevel.v1.SanitizedTransaction",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="message",
            full_name="org.solana.sealevel.v1.SanitizedTransaction.message",
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
            name="message_hash",
            full_name="org.solana.sealevel.v1.SanitizedTransaction.message_hash",
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
            name="is_simple_vote_tx",
            full_name="org.solana.sealevel.v1.SanitizedTransaction.is_simple_vote_tx",
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
        _descriptor.FieldDescriptor(
            name="signatures",
            full_name="org.solana.sealevel.v1.SanitizedTransaction.signatures",
            index=3,
            number=4,
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
    serialized_start=844,
    serialized_end=996,
)
_TXNCONTEXT = _descriptor.Descriptor(
    name="TxnContext",
    full_name="org.solana.sealevel.v1.TxnContext",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="tx",
            full_name="org.solana.sealevel.v1.TxnContext.tx",
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
            name="max_age",
            full_name="org.solana.sealevel.v1.TxnContext.max_age",
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
            name="blockhash_queue",
            full_name="org.solana.sealevel.v1.TxnContext.blockhash_queue",
            index=2,
            number=3,
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
        ),
        _descriptor.FieldDescriptor(
            name="epoch_ctx",
            full_name="org.solana.sealevel.v1.TxnContext.epoch_ctx",
            index=3,
            number=4,
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
            name="slot_ctx",
            full_name="org.solana.sealevel.v1.TxnContext.slot_ctx",
            index=4,
            number=5,
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
    serialized_start=999,
    serialized_end=1223,
)
_RESULTINGSTATE = _descriptor.Descriptor(
    name="ResultingState",
    full_name="org.solana.sealevel.v1.ResultingState",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="acct_states",
            full_name="org.solana.sealevel.v1.ResultingState.acct_states",
            index=0,
            number=1,
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
        _descriptor.FieldDescriptor(
            name="rent_debits",
            full_name="org.solana.sealevel.v1.ResultingState.rent_debits",
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
        _descriptor.FieldDescriptor(
            name="transaction_rent",
            full_name="org.solana.sealevel.v1.ResultingState.transaction_rent",
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
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=1226,
    serialized_end=1381,
)
_RENTDEBITS = _descriptor.Descriptor(
    name="RentDebits",
    full_name="org.solana.sealevel.v1.RentDebits",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="pubkey",
            full_name="org.solana.sealevel.v1.RentDebits.pubkey",
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
            name="rent_collected",
            full_name="org.solana.sealevel.v1.RentDebits.rent_collected",
            index=1,
            number=2,
            type=3,
            cpp_type=2,
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
    serialized_start=1383,
    serialized_end=1435,
)
_FEEDETAILS = _descriptor.Descriptor(
    name="FeeDetails",
    full_name="org.solana.sealevel.v1.FeeDetails",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="transaction_fee",
            full_name="org.solana.sealevel.v1.FeeDetails.transaction_fee",
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
            name="prioritization_fee",
            full_name="org.solana.sealevel.v1.FeeDetails.prioritization_fee",
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
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=1437,
    serialized_end=1502,
)
_TXNRESULT = _descriptor.Descriptor(
    name="TxnResult",
    full_name="org.solana.sealevel.v1.TxnResult",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="executed",
            full_name="org.solana.sealevel.v1.TxnResult.executed",
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
        ),
        _descriptor.FieldDescriptor(
            name="sanitization_error",
            full_name="org.solana.sealevel.v1.TxnResult.sanitization_error",
            index=1,
            number=2,
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
        _descriptor.FieldDescriptor(
            name="resulting_state",
            full_name="org.solana.sealevel.v1.TxnResult.resulting_state",
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
        _descriptor.FieldDescriptor(
            name="rent",
            full_name="org.solana.sealevel.v1.TxnResult.rent",
            index=3,
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
            name="is_ok",
            full_name="org.solana.sealevel.v1.TxnResult.is_ok",
            index=4,
            number=5,
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
        _descriptor.FieldDescriptor(
            name="status",
            full_name="org.solana.sealevel.v1.TxnResult.status",
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
            name="return_data",
            full_name="org.solana.sealevel.v1.TxnResult.return_data",
            index=6,
            number=7,
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
            name="executed_units",
            full_name="org.solana.sealevel.v1.TxnResult.executed_units",
            index=7,
            number=8,
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
            name="accounts_data_len_delta",
            full_name="org.solana.sealevel.v1.TxnResult.accounts_data_len_delta",
            index=8,
            number=9,
            type=3,
            cpp_type=2,
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
            name="fee_details",
            full_name="org.solana.sealevel.v1.TxnResult.fee_details",
            index=9,
            number=10,
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
    serialized_start=1505,
    serialized_end=1807,
)
_TXNFIXTURE = _descriptor.Descriptor(
    name="TxnFixture",
    full_name="org.solana.sealevel.v1.TxnFixture",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="input",
            full_name="org.solana.sealevel.v1.TxnFixture.input",
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
            name="output",
            full_name="org.solana.sealevel.v1.TxnFixture.output",
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
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=1809,
    serialized_end=1923,
)
_TRANSACTIONMESSAGE.fields_by_name["header"].message_type = _MESSAGEHEADER
_TRANSACTIONMESSAGE.fields_by_name["account_shared_data"].message_type = (
    context__pb2._ACCTSTATE
)
_TRANSACTIONMESSAGE.fields_by_name["instructions"].message_type = _COMPILEDINSTRUCTION
_TRANSACTIONMESSAGE.fields_by_name["address_table_lookups"].message_type = (
    _MESSAGEADDRESSTABLELOOKUP
)
_TRANSACTIONMESSAGE.fields_by_name["loaded_addresses"].message_type = _LOADEDADDRESSES
_SANITIZEDTRANSACTION.fields_by_name["message"].message_type = _TRANSACTIONMESSAGE
_TXNCONTEXT.fields_by_name["tx"].message_type = _SANITIZEDTRANSACTION
_TXNCONTEXT.fields_by_name["epoch_ctx"].message_type = context__pb2._EPOCHCONTEXT
_TXNCONTEXT.fields_by_name["slot_ctx"].message_type = context__pb2._SLOTCONTEXT
_RESULTINGSTATE.fields_by_name["acct_states"].message_type = context__pb2._ACCTSTATE
_RESULTINGSTATE.fields_by_name["rent_debits"].message_type = _RENTDEBITS
_TXNRESULT.fields_by_name["resulting_state"].message_type = _RESULTINGSTATE
_TXNRESULT.fields_by_name["fee_details"].message_type = _FEEDETAILS
_TXNFIXTURE.fields_by_name["input"].message_type = _TXNCONTEXT
_TXNFIXTURE.fields_by_name["output"].message_type = _TXNRESULT
DESCRIPTOR.message_types_by_name["MessageHeader"] = _MESSAGEHEADER
DESCRIPTOR.message_types_by_name["CompiledInstruction"] = _COMPILEDINSTRUCTION
DESCRIPTOR.message_types_by_name["MessageAddressTableLookup"] = (
    _MESSAGEADDRESSTABLELOOKUP
)
DESCRIPTOR.message_types_by_name["LoadedAddresses"] = _LOADEDADDRESSES
DESCRIPTOR.message_types_by_name["TransactionMessage"] = _TRANSACTIONMESSAGE
DESCRIPTOR.message_types_by_name["SanitizedTransaction"] = _SANITIZEDTRANSACTION
DESCRIPTOR.message_types_by_name["TxnContext"] = _TXNCONTEXT
DESCRIPTOR.message_types_by_name["ResultingState"] = _RESULTINGSTATE
DESCRIPTOR.message_types_by_name["RentDebits"] = _RENTDEBITS
DESCRIPTOR.message_types_by_name["FeeDetails"] = _FEEDETAILS
DESCRIPTOR.message_types_by_name["TxnResult"] = _TXNRESULT
DESCRIPTOR.message_types_by_name["TxnFixture"] = _TXNFIXTURE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
MessageHeader = _reflection.GeneratedProtocolMessageType(
    "MessageHeader",
    (_message.Message,),
    dict(DESCRIPTOR=_MESSAGEHEADER, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(MessageHeader)
CompiledInstruction = _reflection.GeneratedProtocolMessageType(
    "CompiledInstruction",
    (_message.Message,),
    dict(DESCRIPTOR=_COMPILEDINSTRUCTION, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(CompiledInstruction)
MessageAddressTableLookup = _reflection.GeneratedProtocolMessageType(
    "MessageAddressTableLookup",
    (_message.Message,),
    dict(DESCRIPTOR=_MESSAGEADDRESSTABLELOOKUP, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(MessageAddressTableLookup)
LoadedAddresses = _reflection.GeneratedProtocolMessageType(
    "LoadedAddresses",
    (_message.Message,),
    dict(DESCRIPTOR=_LOADEDADDRESSES, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(LoadedAddresses)
TransactionMessage = _reflection.GeneratedProtocolMessageType(
    "TransactionMessage",
    (_message.Message,),
    dict(DESCRIPTOR=_TRANSACTIONMESSAGE, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(TransactionMessage)
SanitizedTransaction = _reflection.GeneratedProtocolMessageType(
    "SanitizedTransaction",
    (_message.Message,),
    dict(DESCRIPTOR=_SANITIZEDTRANSACTION, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(SanitizedTransaction)
TxnContext = _reflection.GeneratedProtocolMessageType(
    "TxnContext",
    (_message.Message,),
    dict(DESCRIPTOR=_TXNCONTEXT, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(TxnContext)
ResultingState = _reflection.GeneratedProtocolMessageType(
    "ResultingState",
    (_message.Message,),
    dict(DESCRIPTOR=_RESULTINGSTATE, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(ResultingState)
RentDebits = _reflection.GeneratedProtocolMessageType(
    "RentDebits",
    (_message.Message,),
    dict(DESCRIPTOR=_RENTDEBITS, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(RentDebits)
FeeDetails = _reflection.GeneratedProtocolMessageType(
    "FeeDetails",
    (_message.Message,),
    dict(DESCRIPTOR=_FEEDETAILS, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(FeeDetails)
TxnResult = _reflection.GeneratedProtocolMessageType(
    "TxnResult", (_message.Message,), dict(DESCRIPTOR=_TXNRESULT, __module__="txn_pb2")
)
_sym_db.RegisterMessage(TxnResult)
TxnFixture = _reflection.GeneratedProtocolMessageType(
    "TxnFixture",
    (_message.Message,),
    dict(DESCRIPTOR=_TXNFIXTURE, __module__="txn_pb2"),
)
_sym_db.RegisterMessage(TxnFixture)
