import test_suite.invoke_pb2 as elf_pb
from argparse import ArgumentParser
from pathlib import Path

"""
This script can either convert an ELF binary to a ELFLoaderCtx protobuf message (bin2ctx) or 
convert a ELFLoaderCtx back to an ELF binary (ctx2bin) depending on the subcommand used.
The output file will have the same name as the input file but will change the extension based on the operation.
If an output directory is not specified, the output will be saved in the same directory as the input file.
"""


def bin2ctx(bin_paths: list[Path], out_dir: Path | None = None):
    for elf_path in bin_paths:
        out_path = out_dir or elf_path.parent
        with open(elf_path, "rb") as f:
            name = elf_path.stem
            elfctx = elf_pb.ELFLoaderCtx()
            elfctx.elf.data = f.read()

            with open(out_path / (name + ".elfctx"), "wb") as f:
                f.write(elfctx.SerializeToString())
        print(f"Converted {elf_path} to {out_path / (name + '.elfctx')}")


def ctx2bin(ctx_paths: list[Path], out_dir: Path | None = None):
    for ctx_path in ctx_paths:
        out_path = out_dir or ctx_path.parent
        with open(ctx_path, "rb") as f:
            name = ctx_path.stem
            elfctx = elf_pb.ELFLoaderCtx()
            elfctx.ParseFromString(f.read())

            with open(out_path / (name + ".elf"), "wb") as f:
                f.write(elfctx.elf.data)
        print(f"Converted {ctx_path} to {out_path / (name + '.elf')}")


def setup_parser():
    parser = ArgumentParser(description="ELF file conversion tool")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Subcommand to run"
    )

    # Subcommand bin2ctx
    parser_bin2ctx = subparsers.add_parser(
        "bin2ctx", help="Convert binary ELF to ELFLoaderCtx"
    )
    parser_bin2ctx.add_argument(
        "elf_paths", type=Path, nargs="+", help="Paths to the ELF binaries"
    )
    parser_bin2ctx.add_argument("-o", "--out_dir", type=Path, help="Output directory")

    # Subcommand ctx2bin
    parser_ctx2bin = subparsers.add_parser(
        "ctx2bin", help="Convert ELFLoaderCtx to binary ELF"
    )
    parser_ctx2bin.add_argument(
        "ctx_paths", type=Path, nargs="+", help="Paths to the ELFLoaderCtx files"
    )
    parser_ctx2bin.add_argument("-o", "--out_dir", type=Path, help="Output directory")

    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    if args.command == "bin2ctx":
        bin2ctx(args.elf_paths, args.out_dir)
    elif args.command == "ctx2bin":
        ctx2bin(args.ctx_paths, args.out_dir)


if __name__ == "__main__":
    main()
