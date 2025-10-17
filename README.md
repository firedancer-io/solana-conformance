# Solana Conformance Suite

This tool allows for validation of targets (e.g. Firedancer) against Solana Agave by running it against a series of predefined tests. It takes either binary or human-readable Protobuf messages as inputs and runs them through the specified targets. It also includes functionality to validate targets for other issues, such as memory corruption.

## Requirements

This tool works on RHEL8 or Ubuntu.

## Installation

Clone this repository and, for RHEL8, run:

```sh
source install.sh
```

For Ubuntu, run:

```sh
source install_ubuntu.sh
```

### Install auto-completion

```sh
solana-conformance --install-completion
```
You will need to reload your shell + the `test_suite_env` venv to see the changes.

## Currently Supported Harness Types
`list-harness-types` will provide the most updated list.
```
$ solana-conformance list-harness-types

Available harness types:
- ElfLoaderHarness
- InstrHarness
- SyscallHarness
- VmInterpHarness
- VmValidateHarness
- TxnHarness
- BlockHarness
- TypeHarness
```

## Protobuf

Each target must contain a function entrypoint that takes in a Context input message and outputs a Effects message (see [`proto/invoke.proto`](https://github.com/firedancer-io/protosol/blob/main/proto/invoke.proto) as an example).

```
Function Entrypoints:
- ElfLoaderHarness: sol_compat_elf_loader_v1
- InstrHarness: sol_compat_instr_execute_v1
- SyscallHarness: sol_compat_vm_syscall_execute_v1
- VmInterpHarness: sol_compat_vm_interp_v1
- VmValidateHarness: sol_compat_vm_validate_v1
- TxnHarness: sol_compat_txn_execute_v1
- BlockHarness: sol_compat_block_execute_v1
- TypeHarness: sol_compat_type_execute_v1
```

### Updating definitions
All message definitions are defined in [protosol](https://github.com/firedancer-io/protosol/). Anytime, protofuf definitions are updated in protosol, you will need to run the following command:

```sh
./fetch_and_generate.sh
```

### `PROTO_VERSION`
To avoid breakages, we enforce strict proto versioning using git tags.

Specifies the git tag/branch of the [`protosol`](https://github.com/firedancer-io/protosol) repository to use when fetching `.proto` files.

**Default:** set directly in `fetch_and_generate.sh`

**Usage:**
You can override the version for a one-off build:
```bash
PROTO_VERSION=v1.1.0 ./fetch_and_generate.sh
```

## Setting up Environment
To setup the `solana-conformance` environment, run the following command and you will be all set:
```
source test_suite_env/bin/activate
```

## Usage
Run the following to view all supported commands or refer to [commands.md](commands.md):
```
solana-conformance --help
```

### Preferred Debugging
Use the following command instead if you want the ability to debug in GDB:
```
<gdb / rust-gdb> --args python3.11 -m test_suite.test_suite exec-instr --input <input_file> --target <shared_lib>
```
Refer to [`exec-instr`](commands.md#solana-conformance-exec-instr) command for more information.

Recommended usage is opening two terminals side by side, and running the above command on the same output while changing the target parameter to the two desired targets and  stepping through the debugger for each corresponding test case.


### Uninstalling

```sh
source clean.sh
```
