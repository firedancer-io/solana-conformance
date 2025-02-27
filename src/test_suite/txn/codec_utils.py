import fd58
from test_suite.context.codec_utils import decode_acct_state, encode_acct_state
import test_suite.txn_pb2 as txn_pb


def decode_sanitized_tx(tx: txn_pb.SanitizedTransaction):
    # Message hash
    tx.message_hash = fd58.dec32(tx.message_hash or bytes([0] * 32))

    # Signatures
    for i in range(len(tx.signatures)):
        if tx.signatures[i]:
            tx.signatures[i] = fd58.dec64(tx.signatures[i])

    # Account keys
    for i in range(len(tx.message.account_keys)):
        if tx.message.account_keys[i]:
            tx.message.account_keys[i] = fd58.dec32(tx.message.account_keys[i])

    # Recent blockhash
    tx.message.recent_blockhash = fd58.dec32(
        tx.message.recent_blockhash or bytes([0] * 32)
    )

    # Address table lookups
    for i in range(len(tx.message.address_table_lookups)):
        if tx.message.address_table_lookups[i].account_key:
            tx.message.address_table_lookups[i].account_key = fd58.dec32(
                tx.message.address_table_lookups[i].account_key
            )


def encode_sanitized_tx(tx: txn_pb.SanitizedTransaction):
    # Message hash
    tx.message_hash = fd58.enc32(tx.message_hash or bytes([0] * 32))

    # Signatures
    for i in range(len(tx.signatures)):
        if tx.signatures[i]:
            tx.signatures[i] = fd58.enc64(tx.signatures[i])

    # Account keys
    for i in range(len(tx.message.account_keys)):
        if tx.message.account_keys[i]:
            tx.message.account_keys[i] = fd58.enc32(tx.message.account_keys[i])

    # Recent blockhash
    tx.message.recent_blockhash = fd58.enc32(
        tx.message.recent_blockhash or bytes([0] * 32)
    )

    # Address table lookups
    for i in range(len(tx.message.address_table_lookups)):
        if tx.message.address_table_lookups[i].account_key:
            tx.message.address_table_lookups[i].account_key = fd58.enc32(
                tx.message.address_table_lookups[i].account_key
            )


def decode_input(txn_context: txn_pb.TxnContext):
    """
    Decode TxnContext fields in-place into binary, digestable format.
    Addresses are decoded from base58.

    Args:
        - txn_context (txn_pb.TxnContext): Transaction context (will be modified).
    """
    decode_sanitized_tx(txn_context.tx)

    # Blockhash queue
    for i in range(len(txn_context.blockhash_queue)):
        txn_context.blockhash_queue[i] = fd58.dec32(txn_context.blockhash_queue[i])

    # Account shared data
    for i in range(len(txn_context.account_shared_data)):
        decode_acct_state(txn_context.account_shared_data[i])


def encode_input(txn_context: txn_pb.TxnContext):
    """
    Encode TxnContext fields in-place into human-readable format.
    Addresses are encoded to base58.

    Args:
        - txn_context (txn_pb.TxnContext): Transaction context (will be modified).
    """
    encode_sanitized_tx(txn_context.tx)

    # Blockhash queue
    for i in range(len(txn_context.blockhash_queue)):
        txn_context.blockhash_queue[i] = fd58.enc32(txn_context.blockhash_queue[i])

    # Account shared data
    for i in range(len(txn_context.account_shared_data)):
        encode_acct_state(txn_context.account_shared_data[i])


def encode_output(txn_result: txn_pb.TxnResult):
    """
    Encode TxnResult fields in-place into human-readable format.
    Addresses are encoded in base58.

    Args:
        - txn_result (txn_pb.TxnResult): Transaction result (will be modified).
    """

    # Account states
    for i in range(len(txn_result.resulting_state.acct_states)):
        encode_acct_state(txn_result.resulting_state.acct_states[i])
