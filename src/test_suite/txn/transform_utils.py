import fd58
import test_suite.txn_pb2 as txn_pb
import test_suite.context_pb2 as context_pb


def transform_fixture(fixture: txn_pb.TxnFixture):
    """
    Example: migrating the location of the `account_shared_data` in the TxnContext:

    account_shared_data = fixture.input.tx.message.account_shared_data
    shared_data = []
    for account in account_shared_data:
        acct = context_pb.AcctState()
        acct.CopyFrom(account)
        shared_data.append(acct)

    del fixture.input.account_shared_data[:]
    del fixture.input.tx.message.account_shared_data[:]

    fixture.input.account_shared_data.extend(shared_data)
    """
    pass
