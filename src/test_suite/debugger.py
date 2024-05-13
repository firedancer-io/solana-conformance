import ctypes
import multiprocessing
from multiprocessing import Pipe
import signal
import subprocess
import os
from test_suite.multiprocessing_utils import (
    initialize_process_output_buffers,
    process_instruction,
    process_syscall,
)


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
    process_syscall(lib, test_input)
    lib.sol_compat_fini()


def debug_host(shared_library, instruction_context, gdb):
    # Sets up the following debug environment:
    #
    #   +-------------------------------+
    #   | Main Python Process           |
    #   | (this function)               |
    #   |                               |
    #   |   +-----------------------+   |
    #   |   | Child Python Process  |   |
    #   |   | (With sol_compat lib) |   |
    #   |   +-----------------------+   |
    #   |      /\ Attached to           |
    #   |   +-----------------------+   |
    #   |   | Debugger Process      |   |
    #   |   +-----------------------+   |
    #   |                               |
    #   +-------------------------------+

    # Spawn the Python interpreter
    pipe, child_pipe = Pipe()
    target = multiprocessing.Process(
        target=debug_target, args=(shared_library, instruction_context, child_pipe)
    )
    target.start()
    # Wait for a signal that the child process is ready
    assert pipe.recv() == "started"

    commands = [
        # Skip loading Python interpreter libraries, as those are not interesting
        "set auto-solib-add off",
        # Attach to the debug target Python process
        f"attach {target.pid}",
        # As soon as the target library gets loaded, set a breakpoint
        # for the newly appeared executor function
        "set breakpoint pending on",
        "break sol_compat_vm_syscall_execute_v1",
        # "break fd_exec_vm_syscall_test_run",
        # GDB stops the process when attaching, let it continue
        "continue",
        # ... At this point, the child process has SIGSTOP'ed itself
        "set auto-solib-add on",
        # Continue it
        "signal SIGCONT",
        # ... At this point, the child process has dlopen()ed the
        #     target library and the breakpoint was hit
        "layout src",
    ]
    invoke = [gdb, "-q"] + ["--eval-command=" + cmd for cmd in commands]
    print(f"Running {' '.join(invoke)}")
    subprocess.run(invoke)
