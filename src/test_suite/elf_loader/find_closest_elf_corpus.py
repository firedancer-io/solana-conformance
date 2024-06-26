from pathlib import Path
import subprocess as sp
import argparse

REPO_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
CORPUS_PATH = REPO_DIR / Path("corpus_v3_full")
DIFF_BIN = SCRIPT_DIR / Path("diff_bin")

"""
This script finds the closest .elf file in the corpus dir to the given elf file.
It uses diff_bin to compare the two files and count the number of different lines.
The file with the least number of different lines is considered the closest.

Assumes:
1. Original/Unmodified elf file is in the corpus dir with ".elf" extension. 
    Mutated elf files generated by the fuzzer lack extension
"""


def find_closest_elf_corpus(elf_path: Path):
    closest_elf_path = None
    closest_diff = int(1e9)
    for corpus_elf_path in CORPUS_PATH.glob("*.elf"):
        diff_res = sp.run(
            [
                str(DIFF_BIN),
                str(elf_path),
                str(corpus_elf_path),
                "-y",
                "--suppress-common-lines",
            ],
            capture_output=True,
        )
        diff = int(len(diff_res.stdout.decode("utf-8").split("\n")))
        print(diff)
        if diff < closest_diff:
            closest_diff = diff
            closest_elf_path = corpus_elf_path

    return closest_elf_path, closest_diff


def main():

    parser = argparse.ArgumentParser(
        description="Find the closest elf file in the corpus"
    )
    parser.add_argument("elf_path", type=Path, help="Path to the elf file")
    args = parser.parse_args()
    closest_elf_path, diff_lines = find_closest_elf_corpus(args.elf_path)
    print(f"closest file is {closest_elf_path} with {diff_lines} diff lines")


if __name__ == "__main__":
    main()
