from test_suite.fuzz_interface import HarnessCtx
import test_suite.invoke_pb2 as pb
from .codec_utils import decode_input, encode_input, encode_output

InstrHarness = HarnessCtx(
    fuzz_fn_name="sol_compat_instr_execute_v1",
    fixture_desc=pb.InstrFixture.DESCRIPTOR,
    context_human_encode_fn=encode_input,
    context_human_decode_fn=decode_input,
    effects_human_encode_fn=encode_output,
)
