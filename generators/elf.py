import fd58
import hashlib
import test_suite.elf_pb2 as elf_pb
from dataclasses import dataclass
import binascii
import requests
import json
import os

OUTPUT_DIR = "./test-vectors/elf/tests"


# manual code cov
test_vectors = [
    {
        "elf_path": "../firedancer/src/ballet/sbpf/fixtures/hello_solana_program.so",
        "features": [],
        "deploy_checks": False,
    }
]
# fmt: on


def list_dir_recursive_os_walk(start_path="."):
    """
    Recursively lists all files and directories starting from start_path using os.walk().
    """
    for root, dirs, files in os.walk(start_path):
        # print(f"Directory: {root}")
        # for d in dirs:
        #     print(f"  Subdirectory: {os.path.join(root, d)}")
        for f in files:
            # print(f"  File: {os.path.join(root, f)}")
            if f.endswith(".elf"):
                # print(f"  File: {os.path.join(root, f)}")
                yield (root, f)


def _into_key_data(key_prefix, test_vectors):
    return [(key_prefix + str(j), data) for j, data in enumerate(test_vectors)]


print("Generating ELF tests...")

test_vectors = _into_key_data("e", test_vectors)

# for key, test in test_vectors:
#     elf_ctx = elf_pb.ELFLoaderCtx()

#     with open(test.get("elf_path"), "rb") as f:
#         elf_ctx.elf.data = f.read()
#     elf_ctx.features.features.extend(test.get("features", []))
#     elf_ctx.deploy_checks = test.get("deploy_checks", False)

#     serialized_elf = elf_ctx.SerializeToString(deterministic=True)
#     filename = str(key) + "_" + hashlib.sha3_256(serialized_elf).hexdigest()[:16]
#     with open(f"{OUTPUT_DIR}/{filename}.bin", "wb") as f:
#         f.write(serialized_elf)

for root, file in list_dir_recursive_os_walk("../solana-programs/programs/mainnet"):
    elf_ctx = elf_pb.ELFLoaderCtx()

    with open(os.path.join(root, file), "rb") as f:
        elf_ctx.elf.data = f.read()
    elf_ctx.features.features.extend([])
    elf_ctx.deploy_checks = False

    filename = file.replace(".elf", "")

    serialized_elf = elf_ctx.SerializeToString(deterministic=True)
    with open(f"{OUTPUT_DIR}/d0_{filename}.bin", "wb") as f:
        f.write(serialized_elf)

    elf_ctx.deploy_checks = True
    serialized_elf = elf_ctx.SerializeToString(deterministic=True)
    with open(f"{OUTPUT_DIR}/d1_{filename}.bin", "wb") as f:
        f.write(serialized_elf)

print("done!")
