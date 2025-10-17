from enum import Enum
import test_suite.protos.elf_pb2 as elf_pb
from argparse import ArgumentParser
from pathlib import Path
from typing import Callable
from google.protobuf.message import DecodeError

"""
This script can either convert an ELF binary to a ELFLoaderCtx protobuf message (bin2ctx) or 
convert a ELFLoaderCtx back to an ELF binary (ctx2bin) depending on the subcommand used.
The output file will have the same name as the input file but will change the extension based on the operation.
If an output directory is not specified, the output will be saved in the same directory as the input file.
"""


class PBTypes(Enum):
    ELFLoaderCtx = 1
    ELFLoaderEffects = 2
    ELFLoaderFixture = 3


# Normalize loading of protobuf messages
class ElfProto:
    def __init__(self, proto_file: Path):
        self.proto_file = proto_file
        with open(proto_file, "rb") as f:
            data = f.read()

        # Try to parse as ELFLoaderCtx
        elfctx = elf_pb.ELFLoaderCtx()
        try:
            elfctx.ParseFromString(data)
            self.proto = elfctx
            self.ctx = elfctx
            return
        except DecodeError:
            pass

        # Try to parse as ELFLoaderFixture
        elffixture = elf_pb.ELFLoaderFixture()
        try:
            elffixture.ParseFromString(data)
            self.proto = elffixture
            self.ctx = elffixture.input
            self.effects = elffixture.output
            return
        except DecodeError:
            pass

        effects = elf_pb.ELFLoaderEffects()
        try:
            effects.ParseFromString(data)
            self.proto = effects
            self.effects = effects
            return
        except DecodeError:
            pass

        raise ValueError(f"Failed to parse {proto_file}")

    def serialize(self):
        return self.proto.SerializeToString()


def bin2ctx(bin_paths: list[Path], out_dir: Path | None = None):
    for elf_path in bin_paths:
        out_path = out_dir or elf_path.parent
        with open(elf_path, "rb") as f:
            name = elf_path.stem
            elfctx = elf_pb.ELFLoaderCtx()
            elfctx.elf.data = f.read()
            elfctx.elf_sz = len(elfctx.elf.data)

            with open(out_path / (name + ".elfctx"), "wb") as f:
                f.write(elfctx.SerializeToString())
        print(
            f"Converted {elf_path} to {out_path / (name + '.elfctx')} of size {elfctx.elf_sz} bytes"
        )


def ctx2bin(ctx_paths: list[Path], out_dir: Path | None = None):
    for ctx_path in ctx_paths:
        out_path = out_dir or ctx_path.parent
        name = ctx_path.stem
        proto = ElfProto(ctx_path)

        with open(out_path / (name + ".elf"), "wb") as f:
            f.write(proto.ctx.elf.data)
        print(f"Converted {ctx_path} to {out_path / (name + '.elf')}")


def ctx_fill_sz(ctx: elf_pb.ELFLoaderCtx):
    """
    Check if field elf_sz is non-zero. If not, set it to the length of the elf data.
    Non-zero implies size has been set, whether actual size or mutated/fuzzed size.
    We don't want to change that.
    """
    if ctx.elf_sz != 0:
        return
    ctx.elf_sz = len(ctx.elf.data)


ELFCtxTouchupFn = Callable[[elf_pb.ELFLoaderCtx], None]

ctx_touchup_funcs: list[ELFCtxTouchupFn] = [ctx_fill_sz]


def ctx_touchup(ctx_paths: list[Path], out_dir: Path | None = None):
    for ctx_path in ctx_paths:
        out_path = out_dir or ctx_path.parent
        name = ctx_path.stem
        proto = ElfProto(ctx_path)

        for func in ctx_touchup_funcs:
            func(proto.ctx)

        with open(out_path / (name + ".elfctx"), "wb") as f:
            f.write(proto.serialize())
        print(
            f"Filled size for {ctx_path} and saved to {out_path / (name + '.elfctx')}"
        )


def add_subcommand(subparsers, name, help_text, paths_help):
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("paths", type=Path, nargs="+", help=paths_help)
    parser.add_argument("-o", "--out_dir", type=Path, help="Output directory")


def setup_parser():
    parser = ArgumentParser(description="ELF file conversion tool")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Subcommand to run"
    )

    add_subcommand(
        subparsers,
        "bin2ctx",
        "Convert binary ELF to ELFLoaderCtx",
        "Paths to the ELF binaries",
    )
    add_subcommand(
        subparsers,
        "ctx2bin",
        "Convert ELFLoaderCtx to binary ELF",
        "Paths to the ELFLoaderCtx files",
    )
    add_subcommand(
        subparsers,
        "ctx-touchup",
        "Touchup an outdated ELFLoaderCtx. Useful if new fields were added.",
        "Paths to the ELFLoaderCtx files",
    )
    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    if args.command == "bin2ctx":
        bin2ctx(args.paths, args.out_dir)
    elif args.command == "ctx2bin":
        ctx2bin(args.paths, args.out_dir)
    elif args.command == "ctx-touchup":
        ctx_touchup(args.paths, args.out_dir)


if __name__ == "__main__":
    main()
