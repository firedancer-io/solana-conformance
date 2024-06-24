import subprocess
import os
import sys


def set_ld_preload_asan():
    # Run ldconfig -p and capture output
    ldconfig_output = subprocess.check_output(["ldconfig", "-p"], text=True)

    # Filter lines containing "asan"
    asan_libs = [line for line in ldconfig_output.split("\n") if "asan" in line]

    # Extract the first library path if available
    if asan_libs:
        first_asan_lib = asan_libs[0].split()[-1]
    else:
        print("No ASAN library found.")
        return

    # Set LD_PRELOAD environment variable
    os.environ["LD_PRELOAD"] = first_asan_lib
    print(f"LD_PRELOAD set to {first_asan_lib}")
    os.execvp(sys.argv[0], sys.argv)
