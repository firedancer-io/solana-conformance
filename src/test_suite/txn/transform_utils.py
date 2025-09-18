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
    accounts = fixture.input.account_shared_data

    # Get the clock slot
    clock_slot = 10
    for i in range(len(accounts)):
        if accounts[i].address == fd58.dec32(
            b"SysvarC1ock11111111111111111111111111111111"
        ):
            data_array = bytearray(accounts[i].data)

            if len(data_array) < 8:
                continue

            data_array[4] = data_array[4] & 0x00
            data_array[5] = data_array[5] & 0x00
            data_array[6] = data_array[6] & 0x00
            data_array[7] = data_array[7] & 0x00

            accounts[i].data = bytes(data_array)

            clock_slot = int.from_bytes(data_array[:8], "little")

    # Set clock slot
    fixture.input.slot_ctx.slot = clock_slot

    for i in range(len(accounts)):
        if accounts[i].owner != fd58.dec32(
            b"BPFLoaderUpgradeab1e11111111111111111111111"
        ):
            continue

        if len(accounts[i].data) < 12:
            continue

        if (
            accounts[i].data[0] != 3
            and accounts[i].data[1] != 0
            and accounts[i].data[2] != 0
            and accounts[i].data[3] != 0
        ):
            continue

        offset = 4
        slot_array = bytearray(accounts[i].data[offset : offset + 8])
        deployment_slot = int.from_bytes(slot_array, "little")

        if deployment_slot > clock_slot:
            deployment_slot = 0 if clock_slot == 0 else clock_slot

        accounts[i].data = (
            accounts[i].data[:offset]
            + deployment_slot.to_bytes(8, "little")
            + accounts[i].data[offset + 8 :]
        )

    for i in range(len(accounts)):
        if accounts[i].owner != fd58.dec32(
            b"LoaderV411111111111111111111111111111111111"
        ):
            continue

        if len(accounts[i].data) < 8:
            continue

        offset = 0
        slot_array = bytearray(accounts[i].data[offset : offset + 8])
        deployment_slot = int.from_bytes(slot_array, "little")

        if deployment_slot > clock_slot:
            deployment_slot = 0 if clock_slot == 0 else clock_slot

        accounts[i].data = (
            accounts[i].data[:offset]
            + deployment_slot.to_bytes(8, "little")
            + accounts[i].data[offset + 8 :]
        )
