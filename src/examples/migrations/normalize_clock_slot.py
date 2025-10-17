import fd58
import test_suite.protos.invoke_pb2 as invoke_pb
import test_suite.protos.context_pb2 as context_pb


def transform_fixture(fixture: invoke_pb.InstrFixture):
    accounts = fixture.input.accounts

    for i in range(len(accounts)):
        if accounts[i].address == fd58.dec32(
            b"SysvarC1ock11111111111111111111111111111111"
        ):
            data_array = bytearray(accounts[i].data)
            if len(data_array) < 8:
                return

            # Constrain clock slot range to UINT_MAX
            data_array[4] = data_array[4] & 0x00
            data_array[5] = data_array[5] & 0x00
            data_array[6] = data_array[6] & 0x00
            data_array[7] = data_array[7] & 0x00
            accounts[i].data = bytes(data_array)

            # Re-serialize the clock slot into the clock account data and set it in the slot ctx
            slot_array = bytearray(8)
            slot_array[3] = data_array[3]
            slot_array[2] = data_array[2]
            slot_array[1] = data_array[1]
            slot_array[0] = data_array[0]
            fixture.input.slot_context.slot = int.from_bytes(slot_array, "little")
