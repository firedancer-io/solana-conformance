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
solana-test-suite decode-protobuf --input-dir <input_dir> --output-dir <output_dir>
```

| Argument       | Description                                                                                   |
|----------------|-----------------------------------------------------------------------------------------------|
| `--input-dir`  | Input directory containing instruction context messages in binary format                      |
| `--output-dir` | Output directory for encoded, human-readable instruction context messages                     |


Optionally, instruction context messages may also be left in the original Protobuf binary-encoded format.


### Test Suite

To run the test suite, use the following command:

```sh
solana-test-suite run-tests --input-dir <input_dir> --solana-target <solana_target.so> --target <firedancer> [--target <target_2> ...] --output-dir <log_output_dir> --num-processes <num_processes>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction context messages in a human-readable format |
| `--solana-target` | Path to Solana Agave shared object (.so) target file            |
| `--target`      | Additional shared object (.so) target file paths  |
| `--output-dir`  | Log output directory for test results |
| `--num-processes`  | Number of processes to use |
| `--randomize-output-buffer`| Randomizes bytes in output buffer before shared library execution                                                        |

**Note:** Each `.so` target file name should be unique.

### Analysis

After running tests, it may be helpful to squash log files together to compare multiple outputs side-by-side via `vimdiff`. To do so:

```sh
solana-test-suite consolidate-logs --input-dir <input_dir> --output-dir <output_dir> --chunk-size <chunk_size>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing test results |
| `--output-dir`  | Output directory for consolidated logs |
| `--chunk-size`  | Number of test results per file |

By default, log files are arranged lexicographically based on the test case file name. Each chunked log file is named based on the first test case in that file.


### Validation

Used to detect potential memory corruption issues / inconsistent outputs. The program will run each supplied library `num-iteration` times on the entire test suite. Use the following:

```sh
solana-test-suite check-consistency --input-dir <input_dir> --target <firedancer> [--target <target_2> ...] --output-dir <log_output_dir> --num-iterations <num_iterations> --num-processes <num_processes>
```

| Argument                   | Description                                                                                                              |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `--input-dir`              | Input directory containing instruction context messages in a human-readable format                                       |
| `--target`                 | Additional shared object (.so) target file paths                                                                         |
| `--output-dir`             | Log output directory for test results                                                                                    |
| `--num-iterations`         | Number of consistency iterations to run for each library                                                                 |
| `--num-processes`          | Number of processes to use                                                                                               |
| `--randomize-output-buffer`| Randomizes bytes in output buffer before shared library execution                                                        |


### Uninstalling

```sh
source clean.sh
```
