import fd58
import test_suite.invoke_pb2 as invoke_pb


def transform_fixture(fixture: invoke_pb.InstrFixture):
    """
    Example:

    accounts = fixture.input.accounts

    for i in range(len(accounts)):
        if accounts[i].address == fd58.dec32(b"SysvarC1ock11111111111111111111111111111111"):
            data_array = bytearray(accounts[i].data)
            if (len(data_array) < 8):
                return
            data_array[4] = data_array[4] & 0x00
            data_array[5] = data_array[5] & 0x00
            data_array[6] = data_array[6] & 0x00
            data_array[7] = data_array[7] & 0x00
            accounts[i].data = bytes(data_array)

            slot_array = bytearray(8)
            slot_array[3] = data_array[3]
            slot_array[2] = data_array[2]
            slot_array[1] = data_array[1]
            slot_array[0] = data_array[0]
            fixture.input.slot_context.slot = int.from_bytes(slot_array, "little")
    """
    accounts = fixture.input.accounts

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
    fixture.input.slot_context.slot = clock_slot

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
