import ctypes
import signal
import os
from test_suite.multiprocessing_utils import initialize_process_output_buffers, process_instruction

def debug_target(shared_library, test_input, pipe):
    initialize_process_output_buffers()

    pipe.send("started")
    os.kill(os.getpid(), signal.SIGSTOP)

    lib = ctypes.CDLL(shared_library)
    lib.sol_compat_init()
    process_instruction(lib, test_input)
    lib.sol_compat_fini()

