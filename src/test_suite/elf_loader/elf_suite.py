from pathlib import Path
import shutil
import typer
from .elf_loader_exec import process_elf_loader_ctx
from test_suite.sol_compat import initialize_process_output_buffers
import test_suite.invoke_pb2 as pb
import ctypes

SOL_COMPAT_FN_NAME = "sol_compat_elf_loader_v1"

app = typer.Typer()


@app.command()
def create_fixtures(
    elf_ctx_corpora: Path = typer.Argument(help="Path to the ELFLoaderCtx corpora"),
    solana_so_fp: Path = typer.Option(
        Path("impl/lib/libsolfuzz_agave_v2.0.so"),
        "--solana-target",
        "-s",
    ),
    out_dir: Path = typer.Option(
        Path("elf_test_fixtures"),
        "--out-dir",
        "-o",
    ),
):
    # Create the output directory, if necessary
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lib = ctypes.CDLL(solana_so_fp)
    lib.sol_compat_init()
    initialize_process_output_buffers()

    # Process ELFLoaderCtx corpora
    for elf_ctx_path in elf_ctx_corpora.iterdir():
        with open(elf_ctx_path, "rb") as f:
            elf_ctx_str = f.read()
        elf_loader_effects = process_elf_loader_ctx(lib, elf_ctx_str)
        if elf_loader_effects is None:
            print(f"Failed to process {elf_ctx_path}")
            continue
        elf_fixture = pb.ELFLoaderFixture()
        elf_fixture.input.elf.data = elf_ctx_str
        elf_fixture.output.MergeFrom(elf_loader_effects)

        out_fp = out_dir / (elf_ctx_path.stem + ".fix")
        with open(out_fp, "wb") as f:
            f.write(elf_fixture.SerializeToString())
        print(f"Processed {elf_ctx_path} and saved to {out_fp}")

    lib.sol_compat_fini()
    print("Done")
