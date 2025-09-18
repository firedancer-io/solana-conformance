import fd58
import test_suite.block_pb2 as block_pb
import test_suite.context_pb2 as context_pb


def transform_fixture(fixture: block_pb.BlockFixture):
    """
    Example:
    fixture.input.slot_ctx.fee_rate_governor.target_lamports_per_signature = 10000
    fixture.input.slot_ctx.fee_rate_governor.target_signatures_per_slot = 20000
    fixture.input.slot_ctx.fee_rate_governor.min_lamports_per_signature = 5000
    fixture.input.slot_ctx.fee_rate_governor.max_lamports_per_signature = 100000
    fixture.input.slot_ctx.fee_rate_governor.burn_percent = 50
    fixture.input.slot_ctx.parent_signature_count = 0
    """
    accounts = fixture.input.acct_states

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
