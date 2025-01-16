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
    """
    pass
