import fd58
import test_suite.invoke_pb2 as invoke_pb
import test_suite.vm_pb2 as vm_pb
import test_suite.context_pb2 as context_pb


def transform_fixture(fixture: vm_pb.SyscallFixture):
    """
    Example:

    accounts = fixture.input.instr_ctx.accounts
    program_id = fixture.input.instr_ctx.program_id

    program_account = context_pb.AcctState()
    program_account.address = program_id
    program_account.lamports = 123456789
    program_account.executable = True
    program_account.data = b'\x00' * 100
    program_account.rent_epoch = (1 << 64) - 1
    program_account.owner = fd58.dec32(b"BPFLoaderUpgradeab1e11111111111111111111111")


    for i in range(len(accounts)):
        if accounts[i].address == program_id:
            if accounts[i].owner == fd58.dec32(b"BPFLoader1111111111111111111111111111111111"):
                return
            fixture.input.instr_ctx.accounts[i].CopyFrom(program_account)
            return

    fixture.input.instr_ctx.accounts.extend([program_account])

    Example:

    accounts = fixture.input.instr_ctx.accounts

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
            fixture.input.instr_ctx.slot_context.slot = int.from_bytes(slot_array, "little")
    """

    accounts = fixture.input.instr_ctx.accounts

    for i in range(len(accounts)):
        if accounts[i].address == fd58.dec32(
            b"Stake11111111111111111111111111111111111111"
        ):
            accounts[i].owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            program_data = bytearray([0] * 36)
            program_data[0] = 2

            programdata_address = fd58.dec32(
                b"6WU8Nxarf9fudRK5atWwjLY4vFaw5UrrWhL88qz7iCMJ"
            )
            for j in range(len(programdata_address)):
                program_data[j + 4] = programdata_address[j]

            accounts[i].data = bytes(program_data)

            programdata_exists = False
            for j in range(len(accounts)):
                if accounts[j].address == programdata_address:
                    programdata_exists = True
                    break

            if programdata_exists:
                continue

            # Create the program data account
            programdata_account = context_pb.AcctState()
            programdata_account.address = programdata_address
            programdata_account.owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            new_programdata_data = bytearray([0] * 45)
            new_programdata_data[0] = 3

            with open(
                "/data/mjain/repos/solfuzz/bpf_native_programs/stake_elf.so", "rb"
            ) as f:
                programdata_data = f.read()
                programdata_account.data = (
                    bytes(new_programdata_data) + programdata_data
                )

            accounts.append(programdata_account)

        elif accounts[i].address == fd58.dec32(
            b"AddressLookupTab1e1111111111111111111111111"
        ):
            accounts[i].owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            program_data = bytearray([0] * 36)
            program_data[0] = 2

            programdata_address = fd58.dec32(
                b"4zSpbk5jGQyMmUrqCSjFZbRKwsrMXBPsyTzjhJEAsefG"
            )
            for j in range(len(programdata_address)):
                program_data[j + 4] = programdata_address[j]

            accounts[i].data = bytes(program_data)

            programdata_exists = False
            for j in range(len(accounts)):
                if accounts[j].address == programdata_address:
                    programdata_exists = True
                    break

            if programdata_exists:
                continue

            # Create the program data account
            programdata_account = context_pb.AcctState()
            programdata_account.address = programdata_address
            programdata_account.owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            new_programdata_data = bytearray([0] * 45)
            new_programdata_data[0] = 3

            with open(
                "/data/mjain/repos/solfuzz/bpf_native_programs/alut_elf.so", "rb"
            ) as f:
                programdata_data = f.read()
                programdata_account.data = (
                    bytes(new_programdata_data) + programdata_data
                )

            accounts.append(programdata_account)

        elif accounts[i].address == fd58.dec32(
            b"Config1111111111111111111111111111111111111"
        ):
            accounts[i].owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            program_data = bytearray([0] * 36)
            program_data[0] = 2

            programdata_address = fd58.dec32(
                b"CHKQ74qcDUJbwc4snCEZXL8tV1WQvXqioArLGgUHPZq9"
            )
            for j in range(len(programdata_address)):
                program_data[j + 4] = programdata_address[j]

            accounts[i].data = bytes(program_data)

            programdata_exists = False
            for j in range(len(accounts)):
                if accounts[j].address == programdata_address:
                    programdata_exists = True
                    break

            if programdata_exists:
                continue

            # Create the program data account
            programdata_account = context_pb.AcctState()
            programdata_account.address = programdata_address
            programdata_account.owner = fd58.dec32(
                b"BPFLoaderUpgradeab1e11111111111111111111111"
            )
            new_programdata_data = bytearray([0] * 45)
            new_programdata_data[0] = 3

            with open(
                "/data/mjain/repos/solfuzz/bpf_native_programs/config_elf.so", "rb"
            ) as f:
                programdata_data = f.read()
                programdata_account.data = (
                    bytes(new_programdata_data) + programdata_data
                )

            accounts.append(programdata_account)
