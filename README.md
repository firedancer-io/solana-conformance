# Solana Conformance Suite

This tool allows for validation of targets (e.g. Firedancer) against Solana Agave by running it against a series of predefined tests. It takes binary or human-readable Protobuf messages, as well as FlatBuffers fixtures, as inputs and runs them through the specified targets. It also includes functionality to validate targets for other issues, such as memory corruption.

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

Specifies the git tag/branch of the [`protosol`](https://github.com/firedancer-io/protosol) repository to use when fetching `.proto` and `.fbs` files.

**Default:** `v3.0.0` (set in `fetch_and_generate.sh`) - includes both Protobuf and FlatBuffers schemas

**Usage:**
You can override the version for a one-off build:
```bash
PROTO_VERSION=v3.0.0 ./fetch_and_generate.sh
```

## FlatBuffers

In addition to Protobuf, this tool supports FlatBuffers fixtures (`.fix` files). FlatBuffers fixtures are automatically detected and converted to Protobuf format for processing.

### Supported Formats
- **Protobuf** (`.fix`, `.elfctx`, `.instrctx`, etc.) - Standard format
- **FlatBuffers** (`.fix`) - Auto-detected and converted, used by honggfuzz/solfuzz

### Updating FlatBuffers Definitions

FlatBuffers schemas are also defined in [protosol](https://github.com/firedancer-io/protosol/) (v3.0.0+). The `fetch_and_generate.sh` script generates both Protobuf and FlatBuffers Python bindings:

```sh
./fetch_and_generate.sh
```

Or generate FlatBuffers bindings only:
```sh
./generate_flatbuffers.sh
```

### FlatBuffers Compiler (flatc)

The `ensure_flatc.sh` script finds or installs the `flatc` compiler. It searches:
- `$SOLFUZZ_DIR/bin/flatc`
- `/data/$USER/solfuzz/bin/flatc`
- `/data/$USER/repos/solfuzz/bin/flatc`
- System PATH
- `~/.local/bin/flatc`

```sh
./ensure_flatc.sh
```

### Using FlatBuffers Fixtures

FlatBuffers fixtures work transparently with all commands:

```sh
# Run tests on FlatBuffers fixtures
solana-conformance run-tests -i fixtures/ -s agave.so -t firedancer.so

# Download fixtures from Octane (may be FlatBuffers or Protobuf)
solana-conformance download-fixtures --use-octane -n sol_elf_loader_diff

# Validate fixtures and check their format
solana-conformance validate-fixtures -i fixtures/
solana-conformance validate-fixtures -i fixtures/ -v  # verbose
```

Example output:
```
[OK] bug_3ec6cbcd.fix
     Format: flatbuffers
     Entrypoint: sol_compat_elf_loader_v1
     ELF size: 1702 bytes

Summary: 10 files checked
  Valid:   10
  Invalid: 0
  Formats: 3 Protobuf, 7 FlatBuffers
```

### Python API

```python
from test_suite.flatbuffers_utils import FixtureLoader, detect_format

# Unified loading (auto-detects format)
loader = FixtureLoader(Path('fixture.fix'))
print(f"Format: {loader.format_type}")  # 'flatbuffers' or 'protobuf'
print(f"Entrypoint: {loader.fn_entrypoint}")
print(f"ELF size: {len(loader.elf_data)} bytes")

# Format detection only
with open('fixture.fix', 'rb') as f:
    fmt = detect_format(f.read())  # Returns 'flatbuffers', 'protobuf', or 'unknown'
```

## Octane Integration

Octane is the fuzzing orchestrator that manages bug discovery, validation, and artifact storage. `solana-conformance` can download bugs and fixtures directly from Octane.

### Setup

1. **Install Octane dependencies:**
   ```sh
   pip install -e ".[octane]"
   ```

2. **Configure GCS credentials** (for downloading artifacts from Google Cloud Storage):
   ```sh
   # Option 1: Use gcloud CLI (recommended)
   gcloud auth application-default login
   
   # Option 2: Set credentials path explicitly
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
   ```

3. **Set Octane API endpoint** (optional, defaults to localhost):
   ```sh
   export OCTANE_API_ORIGIN=http://your-octane-server:5000
   ```

### Downloading from Octane

```sh
# Download fixtures (prefers .fix files)
solana-conformance download-fixtures --use-octane -n sol_elf_loader_diff -o fixtures/

# Download crash inputs (prefers .fuzz files)
solana-conformance download-crashes --use-octane -n sol_elf_loader_diff -o crashes/

# Download a single repro by hash
solana-conformance download-repro --use-octane <hash> -l sol_elf_loader_diff -o output/

# Debug a mismatch from Octane
solana-conformance debug-mismatch <hash> -l sol_elf_loader_diff --use-octane \
    -s $SOLFUZZ_TARGET -t $FIREDANCER_TARGET -o debug_output/
```

### File Formats

Octane stores artifacts in two formats:
- **`.fuzz` files** - Raw fuzzer inputs (FlatBuffers format)
- **`.fix` files** - Validated fixtures with expected outputs (FlatBuffers or Protobuf)

`solana-conformance` automatically detects and handles both formats.

### GCS Authentication Troubleshooting

If you see GCS authentication errors:

```sh
# Check current credentials
gcloud auth application-default print-access-token

# Re-authenticate
gcloud auth application-default login

# Verify project
gcloud config get-value project
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

## Troubleshooting

### Check Dependencies

Run the dependency checker to diagnose issues:

```sh
solana-conformance check-deps
```

Example output:
```
=== solana-conformance FlatBuffers Status ===

[OK] flatbuffers package: v24.3.25
[OK] numpy package: v1.26.4 (faster parsing)
[OK] FlatBuffers bindings: generated

[OK] FlatBuffers support is ready!
```

### Common Issues

#### "FlatBuffers support not available"

**Cause:** The `flatbuffers` Python package is not installed.

**Fix:**
```sh
pip install flatbuffers>=24.0.0
# Or re-run the install script:
source install.sh
```

#### "FlatBuffers bindings not generated"

**Cause:** The Python bindings generated from `.fbs` schemas don't exist.

**Fix:**
```sh
./generate_flatbuffers.sh
```

If that fails, ensure `flatc` is available:
```sh
./ensure_flatc.sh
```

#### "Failed to parse fixture" with FlatBuffers file

**Cause:** The fixture file may be corrupted, empty, or in an unexpected format.

**Debug:**
```python
from test_suite.flatbuffers_utils import FixtureLoader
from pathlib import Path

loader = FixtureLoader(Path('problematic.fix'))
print(f"Valid: {loader.is_valid}")
print(f"Format: {loader.format_type}")
print(f"Error: {loader.error_message}")
```

Example error output:
```
Valid: False
Format: unknown
Error: Failed to convert FlatBuffers to Protobuf: problematic.fix
  FlatBuffers conversion error: error: unpack_from requires a buffer of at least 24 bytes...
```

#### "Unable to parse fixture: Not recognized as Protobuf or FlatBuffers"

**Cause:** The file is neither valid Protobuf nor FlatBuffers. It may be:
- A raw `.fuzz` input (not a fixture)
- A corrupted download
- A different file format

**Check file type:**
```sh
file problematic.fix
hexdump -C problematic.fix | head
```

#### Slow FlatBuffers parsing

**Cause:** Numpy is not installed.

**Fix:**
```sh
pip install numpy>=1.24.0
```

With numpy, large ELF data is parsed significantly faster.

#### After `git pull`, FlatBuffers fixtures don't work

**Cause:** Schema updates require regenerating bindings.

**Fix:**
```sh
./fetch_and_generate.sh
```

This fetches the latest protosol schemas and regenerates both Protobuf and FlatBuffers bindings.
