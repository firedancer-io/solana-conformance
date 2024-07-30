# Solana Test Suite

This tool allows for validation of targets (e.g. Firedancer) against Solana Agave by running it against a series of predefined tests. It takes either binary or human-readable Protobuf messages as inputs and runs them through the specified targets. It also includes functionality to validate targets for other issues, such as memory corruption.

## Requirements

This tool only works on RHEL8.

## Installation

Clone this repository and run:

```sh
source install.sh
```

### (HIGHLY Recommended) Install auto-completion

```sh
solana-test-suite --install-completion
```
You will need to reload your shell + the `test_suite_env` venv to see the changes.

## Protobuf

Each target must contain a `sol_compat_instr_execute_v1` function that takes in a `InstrContext` message and outputs a `InstrEffects` message (see [`proto/invoke.proto`](https://github.com/firedancer-io/protosol/blob/main/proto/invoke.proto)). See `utils.py:process_instruction` to see how the program interacts with shared libraries.

### Updating definitions
All message definitions are defined in [Protosol](https://github.com/firedancer-io/protosol/). You may need to periodically update these definitions with the following command:

```sh
./fetch_and_generate.sh
```

## Usage
Run `solana-test-suite --help` to see the available commands. 
Or, refer to the [commands.md](commands.md) for a list of available commands.

### Note on [commands.md](commands.md)
`commands.md` is automatically generated from the `typer utils docs` module.
Help messages are dynamically generated based on the [currently set harness type](#selecting-the-correct-harness). Thus, descriptions specific to harness type (typically the Context, Effects, and Fixtures names) in `commands.md` refer to the harness type set during time of generation.

When the desired [harness type is set](#selecting-the-correct-harness), the `--help` output in the CLI will reflect the correct names. Try it!

### Selecting the correct harness
The harness type should be specified by an environment variable `HARNESS_TYPE` and supports the following values (default is `InstrHarness` if not provided):
- `InstrHarness`
- `TxnHarness`
- `SyscallHarness`
- `ValidateVM`
- `ElfHarness`


### Data Preparation

Before running tests, Context messages may be converted into Protobuf's text format, with all `bytes` fields base58-encoded (for human readability). This can be done with [decode-protobuf](commands.md#solana-test-suite-decode-protobuf) command.

Optionally, context messages may also be left in the original Protobuf binary-encoded format.


### Debugging

For failing test cases, it may be useful to analyze what could have differed between Solana and Firedancer. You can execute a Protobuf message (human-readable or binary) through the desired client with the [`debug-instr`](commands.md#solana-test-suite-debug-instr) command.


#### Alternative (and preferred) debugging solution

Use the following command instead if you want the ability to directly restart the program without having to restart GDB:
```sh
<gdb / rust-gdb> --args python3.11 -m test_suite.test_suite exec-instr --input <input_file> --target <shared_lib>
```

Refer to [`exec-instr`](commands.md#solana-test-suite-exec-instr) command for more information.

Recommended usage is opening two terminals side by side, and running the above command on both with one having `--target` for Solana (`impl/lib/libsolfuzz_agave_v2.0.so`) and another for Firedancer (`impl/lib/libsolfuzz_firedancer.so`), and then stepping through the debugger for each corresponding test case.


### Uninstalling

```sh
source clean.sh
```
