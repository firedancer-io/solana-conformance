import ctypes
import signal
import os
from test_suite.multiprocessing_utils import initialize_process_output_buffers, process_instruction

def debug_target(shared_library, test_input, pipe):
    initialize_process_output_buffers()

    # Signal to parent that we are ready for the debugger
    pipe.send("started")

    # Suspend self so the debugger has time to attach
    os.kill(os.getpid(), signal.SIGSTOP)
    # ... at this point, the debugger has sent us a SIGCONT signal,
    #     is watching any dlopen() call and has set breakpoints

    lib = ctypes.CDLL(shared_library)
    lib.sol_compat_init()
    process_instruction(lib, test_input)
    lib.sol_compat_fini()

