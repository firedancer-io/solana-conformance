# Solana Test Suite

This tool allows for validation of targets (e.g. Firedancer) against Solana Agave by running it against a series of predefined tests. It takes human-readable Protobuf messages as inputs and runs them through the specified targets.

## Installation

Clone this repository and run:

```sh
pip install .
```

## Protobuf

Each target must contain a `sol_compat_instr_execute_v1` function that takes in a `InstrContext` message and outputs a `InstrEffects` message (see `src/test_suite/invoke.proto`). See `utils.py:process_instruction` to see how the program interacts with shared libraries.

## Usage

To run the test suite, use the following command:

```sh
solana-test-suite run-tests --input-dir <input_dir> --solana-target <solana_target.so> --target <firedancer> [--target <target_2> ...] --output-dir <log_output_dir>
```

| Argument        | Description                                                                                         |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `--input-dir`   | Input directory containing instruction context messages in a human-readable format |
| `--solana-target` | Path to Solana Agave shared object (.so) target file            |
| `--target`      | Additional shared object (.so) target file paths  |
| `--output-dir`  | Log output directory for test results |
