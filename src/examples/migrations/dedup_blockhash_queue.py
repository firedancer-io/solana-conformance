import fd58
import test_suite.txn_pb2 as txn_pb
import test_suite.context_pb2 as context_pb


def transform_fixture(fixture: txn_pb.TxnFixture):
    blockhashes = fixture.input.blockhash_queue
    seen_blockhashes = set()
    for i in range(len(blockhashes) - 1, -1, -1):
        if blockhashes[i] in seen_blockhashes:
            del blockhashes[i]
            continue
        seen_blockhashes.add(blockhashes[i])
