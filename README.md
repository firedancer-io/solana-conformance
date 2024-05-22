# Solana Test Suite

This tool allows for validation of targets (e.g. Firedancer) against Solana Agave by running it against a series of predefined tests. It takes either binary or human-readable Protobuf messages as inputs and runs them through the specified targets. It also includes functionality to validate targets for other issues, such as memory corruption.

## Requirements

This tool only works on RHEL8.

## Installation

Clone this repository and run:

```sh
source install.sh
```

## Protobuf

Each target must contain a `sol_compat_instr_execute_v1` function that takes in a `InstrContext` message and outputs a `InstrEffects` message (see `src/test_suite/invoke.proto`). See `utils.py:process_instruction` to see how the program interacts with shared libraries.

## Usage

### Data Preparation

Before running tests, `InstrContext` messages may be converted into Protobuf's text format, with all `bytes` fields base58-encoded (for human readability). Run the following command to do this:

```sh
solana-test-suite decode-protobuf --input-dir <input_dir> --output-dir <output_dir> --num-processes <num_processes>
```

| Argument       | Description                                                                                   |
|----------------|-----------------------------------------------------------------------------------------------|
| `--input-dir`  | Input directory containing instruction context messages in binary format                      |
| `--output-dir` | Output directory for encoded, human-readable instruction context messages                     |
| `--num-processes`  | Number of processes to use |


Optionally, instruction context messages may also be left in the original Protobuf binary-encoded format.


### Test Suite

To run the test suite, use the following command:

```sh
solana-test-suite run-tests --input-dir <input_dir> --solana-target <solana_target.so> --target <firedancer.so> [--target <target_2> ...] --output-dir <log_output_dir> --num-processes <num_processes> --chunk-size <chunk_size> [--randomize-output-buffer]
```

You can provide both `InstrContext` and `InstrFixture` within `--input-dir` - parsing is taken care of depending on the file extension `.bin` for `InstrContext` and `.fix` for `InstrFixture`.

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction context or fixture messages |
| `--solana-target` | Path to Solana Agave shared object (.so) target file            |
| `--target`      | Additional shared object (.so) target file paths  |
| `--output-dir`  | Log output directory for test results |
| `--num-processes`  | Number of processes to use |
| `--randomize-output-buffer`| Randomizes bytes in output buffer before shared library execution                                                        |
| `--chunk-size`  | Number of test results per log file |
| `--verbose`   | Verbose output: log failed test cases |

**Note:** Each `.so` target file name should be unique.


### Single instruction

You can pick out a single test case and run it to view the instruction effects via output with the following command:

```sh
solana-test-suite exec-instr --input <input_file> --target <shared_lib>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input`      | Input file containing instruction context message |
| `--target`      | Shared object (.so) target file path to debug  |


### Debugging

For failing test cases, it may be useful to analyze what could have differed between Solana and Firedancer. You can execute a Protobuf message (human-readable or binary) through the desired client as such:

```sh
solana-test-suite debug-instr --input <input_file> --target <shared_lib> --debugger <gdb,rust-gdb,etc>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input`      | Input file containing instruction context message |
| `--target`      | Shared object (.so) target file path to debug  |
| `--debugger`  | Debugger to use (gdb, rust-gdb) |

Recommended usage is opening two terminals side by side, and running the above command on both with one having `--target` for Solana (`impl/lib/libsolfuzz_agave_v2.0.so`) and another for Firedancer (`impl/lib/libsolfuzz_firedancer.so`), and then stepping through the debugger for each corresponding test case.


### Minimizing

Prunes extra fields in the input (e.g. feature set) and produces a minimal test case such that the output does not change.

```sh
solana-test-suite minimize-tests --input-dir <input_dir> --solana-target <solana_target.so> --output-dir <pruned_ctx_output_dir> --num-processes <num_processes>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction context messages |
| `--solana-target` | Path to Solana Agave shared object (.so) target file            |
| `--output-dir`  | Pruned instruction context dumping directory |
| `--num-processes`  | Number of processes to use |


### Creating Fixtures from Instruction Context

Create full test fixtures containing both instruction context and effects. Effects are computed by running instruction context through `--solana-target`. Fixtures with `None` values for instruction context/effects are not included.

```sh
solana-test-suite create-fixtures --input-dir <input_dir> --solana-target <solana_target.so> --target <firedancer.so> [--target <target_2> ...] --output-dir <fixtures_output_dir> --num-processes <num_processes> [--readable] [--keep-passing] [--group-by-program]
```

You have an additional option to produce fixtures for only passing test cases (makes it easier to produce fixtures from larger batches of new-passing mismatches).


| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction context messages |
| `--solana-target` | Path to Solana Agave shared object (.so) target file            |
| `--target`  | Shared object (.so) target file paths (pairs with `--keep-passing`)
| `--output-dir`  | Instruction fixtures dumping directory |
| `--num-processes`  | Number of processes to use |
| `--readable` | Output fixtures in human-readable format |
| `--keep-passing` | Only keep passing test cases |
| `--group-by-program` | Group fixture output by program type |


### Create Instruction Context from Fixtures

Opposite as above. Does not require a target.

```sh
solana-test-suite instr-from-fixtures --input-dir <input_dir> --solana-target <solana_target.so> --output-dir <fixtures_output_dir> --num-processes <num_processes> [--readable]
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction fixture messages |
| `--output-dir`  | Output directory for instr contexts |
| `--num-processes`  | Number of processes to use |


### Uninstalling

```sh
source clean.sh
```
