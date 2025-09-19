import fd58
import test_suite.invoke_pb2 as invoke_pb
import test_suite.vm_pb2 as vm_pb
import test_suite.context_pb2 as context_pb
import struct


def create_sysvar_account(address: bytes, data: bytes):
    account = context_pb.AcctState()
    account.address = address
    account.lamports = 1
    account.data = data
    account.executable = False
    account.owner = fd58.dec32(b"Sysvar1111111111111111111111111111111111111")
    return account


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

    has_clock = False
    has_epoch_schedule = False
    has_rent = False
    has_last_restart_slot = False
    has_slot_hashes = False
    has_recent_block_hashes = False

    default_slot = 10

    for i in range(len(accounts)):
        if accounts[i].address == fd58.dec32(
            b"SysvarC1ock11111111111111111111111111111111"
        ):
            has_clock = True
            if len(accounts[i].data) < 40:
                accounts[i].data = default_slot.to_bytes(8, "little") + b"\x00" * 32

            slot = int.from_bytes(accounts[i].data[:8], "little")
            fixture.input.instr_ctx.slot_context.slot = slot

        elif accounts[i].address == fd58.dec32(
            b"SysvarEpochSchedu1e111111111111111111111111"
        ):
            has_epoch_schedule = True
            if len(accounts[i].data) < 33:
                accounts[i].data = (
                    int(432000).to_bytes(8, "little")
                    + int(432000).to_bytes(8, "little")
                    + b"\x01"
                    + int(14).to_bytes(8, "little")
                    + int(524256).to_bytes(8, "little")
                )

            warmup = int.from_bytes(accounts[i].data[16:17])
            if warmup > 1:
                warmup = 1

            accounts[i].data = (
                accounts[i].data[:16]
                + warmup.to_bytes(1, "little")
                + accounts[i].data[17:]
            )

        elif accounts[i].address == fd58.dec32(
            b"SysvarRent111111111111111111111111111111111"
        ):
            has_rent = True
            if len(accounts[i].data) < 17:
                accounts[i].data = (
                    int(3480).to_bytes(8, "little")
                    + struct.pack("<d", 2)
                    + int(50).to_bytes(1, "little")
                )

        elif accounts[i].address == fd58.dec32(
            b"SysvarLastRestartS1ot1111111111111111111111"
        ):
            has_last_restart_slot = True
            if len(accounts[i].data) < 8:
                accounts[i].data = int(5000).to_bytes(8, "little")

        elif accounts[i].address == fd58.dec32(
            b"SysvarS1otHashes111111111111111111111111111"
        ):
            has_slot_hashes = True
            accounts[i].data = accounts[i].data[:20488]
            if len(accounts[i].data) < 20488:
                accounts[i].data = accounts[i].data + bytes(
                    20488 - len(accounts[i].data)
                )

        elif accounts[i].address == fd58.dec32(
            b"SysvarRecentB1ockHashes11111111111111111111"
        ):
            has_recent_block_hashes = True
            if len(accounts[i].data) < 8:
                accounts[i].data = int(150).to_bytes(8, "little") + bytes(6000)

        else:
            continue

        if accounts[i].lamports == 0:
            accounts[i].lamports = 1
        accounts[i].executable = False
        accounts[i].owner = fd58.dec32(b"Sysvar1111111111111111111111111111111111111")

    if not has_clock:
        clock_account = create_sysvar_account(
            fd58.dec32(b"SysvarC1ock11111111111111111111111111111111"),
            default_slot.to_bytes(8, "little") + b"\x00" * 32,
        )
        accounts.append(clock_account)
        fixture.input.instr_ctx.slot_context.slot = default_slot

    if not has_epoch_schedule:
        epoch_schedule_account = create_sysvar_account(
            fd58.dec32(b"SysvarEpochSchedu1e111111111111111111111111"),
            int(432000).to_bytes(8, "little")
            + int(432000).to_bytes(8, "little")
            + b"\x01"
            + int(14).to_bytes(8, "little")
            + int(524256).to_bytes(8, "little"),
        )
        accounts.append(epoch_schedule_account)

    if not has_rent:
        rent_account = create_sysvar_account(
            fd58.dec32(b"SysvarRent111111111111111111111111111111111"),
            int(3480).to_bytes(8, "little")
            + struct.pack("<d", 2)
            + int(50).to_bytes(1, "little"),
        )
        accounts.append(rent_account)

    if not has_last_restart_slot:
        last_restart_slot_account = create_sysvar_account(
            fd58.dec32(b"SysvarLastRestartS1ot1111111111111111111111"),
            int(5000).to_bytes(8, "little"),
        )
        accounts.append(last_restart_slot_account)

    if not has_slot_hashes:
        slot_hashes_account = create_sysvar_account(
            fd58.dec32(b"SysvarS1otHashes111111111111111111111111111"),
            bytes(20488),
        )
        accounts.append(slot_hashes_account)

    if not has_recent_block_hashes:
        recent_block_hashes_account = create_sysvar_account(
            fd58.dec32(b"SysvarRecentB1ockHashes11111111111111111111"),
            int(150).to_bytes(8, "little") + bytes(6000),
        )
        accounts.append(recent_block_hashes_account)
