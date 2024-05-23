from pathlib import Path
import shutil
import typer
from test_suite.sol_compat import initialize_process_output_buffers, process_target
import ctypes
from .fuzz_context import *
from test_suite.globals import harness_ctx as h_ctx
import test_suite.globals as globals
from multiprocessing import Pool


app = typer.Typer()

h_ctx = InstrHarness


@app.command()
def create_fixtures(
    ctx_corpora: Path = typer.Argument(
        help=f"Path to the {h_ctx.context_type.__name__} corpora"
    ),
    reference_so_fp: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave_v2.0.so"),
        "--ref-target",
        "-t",
    ),
    out_dir: Path = typer.Option(
        Path("test_fixtures"),
        "--out-dir",
        "-o",
    ),
):
    # Specify globals
    globals.output_dir = out_dir
    globals.reference_shared_library = reference_so_fp
    # globals.readable = readable

    # Create the output directory, if necessary
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lib = ctypes.CDLL(reference_so_fp)
    lib.sol_compat_init()
    initialize_process_output_buffers()
    globals.target_libraries[reference_so_fp] = lib

    # Process corpora
    for ctx_path in ctx_corpora.iterdir():
        with open(ctx_path, "rb") as f:
            ctx_str = f.read()
        effects = process_target(lib, ctx_str, h_ctx)
        if effects is None:
            print(f"Failed to process {ctx_path}")
            continue
        fixture = h_ctx.fixture_type()
        fixture.input.ParseFromString(ctx_str)
        fixture.output.MergeFrom(effects)

        out_fp = out_dir / (ctx_path.stem + ".fix")
        with open(out_fp, "wb") as f:
            f.write(fixture.SerializeToString())
        print(f"Processed {ctx_path} and saved to {out_fp}")

    lib.sol_compat_fini()
    print("Done")
