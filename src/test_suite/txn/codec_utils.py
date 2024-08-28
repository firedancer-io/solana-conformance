import fd58
import test_suite.txn_pb2 as txn_pb


def decode_input(txn_context: txn_pb.TxnContext):
    """
    Decode TxnContext fields in-place into binary, digestable format.
    Addresses are decoded from base58.

    Args:
        - txn_context (txn_pb.TxnContext): Transaction context (will be modified).
    """
    # Message hash
    txn_context.tx.message_hash = fd58.dec32(
        txn_context.tx.message_hash or bytes([0] * 32)
    )

    # Signatures
    for i in range(len(txn_context.tx.signatures)):
        if txn_context.tx.signatures[i]:
            txn_context.tx.signatures[i] = fd58.dec64(txn_context.tx.signatures[i])

    # Account keys
    for i in range(len(txn_context.tx.message.account_keys)):
        if txn_context.tx.message.account_keys[i]:
            txn_context.tx.message.account_keys[i] = fd58.dec32(
                txn_context.tx.message.account_keys[i]
            )

    # Account shared data
    for i in range(len(txn_context.tx.message.account_shared_data)):
        # Pubkey
        if txn_context.tx.message.account_shared_data[i].address:
            txn_context.tx.message.account_shared_data[i].address = fd58.dec32(
                txn_context.tx.message.account_shared_data[i].address
            )

        # Not encoding data because it's not super useful in inspection

        # Owner
        if txn_context.tx.message.account_shared_data[i].owner:
            txn_context.tx.message.account_shared_data[i].owner = fd58.dec32(
                txn_context.tx.message.account_shared_data[i].owner
            )

    # Recent blockhash
    txn_context.tx.message.recent_blockhash = fd58.dec32(
        txn_context.tx.message.recent_blockhash or bytes([0] * 32)
    )

    # Address table lookups
    for i in range(len(txn_context.tx.message.address_table_lookups)):
        if txn_context.tx.message.address_table_lookups[i].account_key:
            txn_context.tx.message.address_table_lookups[i].account_key = fd58.dec32(
                txn_context.tx.message.address_table_lookups[i].account_key
            )

    # Blockhash queue
    for i in range(len(txn_context.blockhash_queue)):
        txn_context.blockhash_queue[i] = fd58.dec32(txn_context.blockhash_queue[i])


def encode_input(txn_context: txn_pb.TxnContext):
    """
    Encode TxnContext fields in-place into human-readable format.
    Addresses are encoded to base58.

    Args:
        - txn_context (txn_pb.TxnContext): Transaction context (will be modified).
    """
    # Message hash
    txn_context.tx.message_hash = fd58.enc32(
        txn_context.tx.message_hash or bytes([0] * 32)
    )

    # Signatures
    for i in range(len(txn_context.tx.signatures)):
        if txn_context.tx.signatures[i]:
            txn_context.tx.signatures[i] = fd58.enc64(txn_context.tx.signatures[i])

    # Account keys
    for i in range(len(txn_context.tx.message.account_keys)):
        if txn_context.tx.message.account_keys[i]:
            txn_context.tx.message.account_keys[i] = fd58.enc32(
                txn_context.tx.message.account_keys[i]
            )

    # Account shared data
    for i in range(len(txn_context.tx.message.account_shared_data)):
        # Pubkey
        if txn_context.tx.message.account_shared_data[i].address:
            txn_context.tx.message.account_shared_data[i].address = fd58.enc32(
                txn_context.tx.message.account_shared_data[i].address
            )

        # Not encoding data because it's not super useful in inspection

        # Owner
        if txn_context.tx.message.account_shared_data[i].owner:
            txn_context.tx.message.account_shared_data[i].owner = fd58.enc32(
                txn_context.tx.message.account_shared_data[i].owner
            )

    # Recent blockhash
    txn_context.tx.message.recent_blockhash = fd58.enc32(
        txn_context.tx.message.recent_blockhash or bytes([0] * 32)
    )

    # Address table lookups
    for i in range(len(txn_context.tx.message.address_table_lookups)):
        if txn_context.tx.message.address_table_lookups[i].account_key:
            txn_context.tx.message.address_table_lookups[i].account_key = fd58.enc32(
                txn_context.tx.message.address_table_lookups[i].account_key
            )

    # Blockhash queue
    for i in range(len(txn_context.blockhash_queue)):
        txn_context.blockhash_queue[i] = fd58.enc32(txn_context.blockhash_queue[i])


def encode_output(txn_result: txn_pb.TxnResult):
    """
    Encode TxnResult fields in-place into human-readable format.
    Addresses are encoded in base58.

    Args:
        - txn_result (txn_pb.TxnResult): Transaction result (will be modified).
    """

    # Account states
    for i in range(len(txn_result.resulting_state.acct_states)):
        # Pubkey
        if txn_result.resulting_state.acct_states[i].address:
            txn_result.resulting_state.acct_states[i].address = fd58.enc32(
                txn_result.resulting_state.acct_states[i].address
            )

        # Not encoding data because it's not super useful in inspection

        # Owner
        if txn_result.resulting_state.acct_states[i].owner:
            txn_result.resulting_state.acct_states[i].owner = fd58.enc32(
                txn_result.resulting_state.acct_states[i].owner
            )
