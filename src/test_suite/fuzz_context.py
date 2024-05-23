from test_suite.fuzz_interface import HarnessCtx
import test_suite.invoke_pb2 as pb


ElfHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_elf_loader_v1", 
    fixture_desc=pb.ELFLoaderFixture.DESCRIPTOR
)
