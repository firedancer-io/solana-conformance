#!/usr/bin/env python3
"""
Setup test data for integration tests.

This script copies a small set of fixtures and contexts from test-vectors
or generates minimal test data if test-vectors are not available.
"""
import argparse
import shutil
import sys
from pathlib import Path


def copy_sample_fixtures(test_vectors_dir: Path, output_dir: Path, max_files: int = 5):
    """Copy a sample of fixtures from test-vectors."""
    fixtures_dir = output_dir / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Find fixture directories in test-vectors
    fixture_patterns = ["**/fixtures/*.fix", "**/fixtures_*/*.fix"]
    fixture_files = []

    for pattern in fixture_patterns:
        fixture_files.extend(test_vectors_dir.glob(pattern))

    if not fixture_files:
        print(f"Warning: No fixtures found in {test_vectors_dir}")
        return 0

    # Copy a sample of fixtures
    copied = 0
    for fixture in fixture_files[:max_files]:
        dest = fixtures_dir / fixture.name
        if not dest.exists():
            shutil.copy2(fixture, dest)
            copied += 1
            print(f"Copied: {fixture.name}")

    return copied


def copy_sample_contexts(test_vectors_dir: Path, output_dir: Path, max_files: int = 5):
    """Copy a sample of context files from test-vectors."""
    contexts_dir = output_dir / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)

    # Find context files in test-vectors
    context_files = list(test_vectors_dir.glob("**/*.bin"))

    if not context_files:
        print(f"Warning: No context files found in {test_vectors_dir}")
        return 0

    # Copy a sample of contexts
    copied = 0
    for context in context_files[:max_files]:
        dest = contexts_dir / context.name
        if not dest.exists():
            shutil.copy2(context, dest)
            copied += 1
            print(f"Copied: {context.name}")

    return copied


def main():
    parser = argparse.ArgumentParser(
        description="Setup test data for integration tests"
    )
    parser.add_argument(
        "--test-vectors",
        type=Path,
        help="Path to test-vectors directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "test_data",
        help="Output directory for test data (default: tests/test_data)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Maximum number of files to copy per category (default: 5)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of test data",
    )

    args = parser.parse_args()

    # Clean output directory if force is specified
    if args.force and args.output.exists():
        print(f"Removing existing test data: {args.output}")
        shutil.rmtree(args.output)

    args.output.mkdir(parents=True, exist_ok=True)

    # Try to find test-vectors directory
    test_vectors = args.test_vectors
    if not test_vectors:
        # Try common locations
        candidates = [
            Path.home() / "code/test-vectors",
            Path("../test-vectors"),
            Path("../../test-vectors"),
        ]
        for candidate in candidates:
            if candidate.exists():
                test_vectors = candidate
                break

    if not test_vectors or not test_vectors.exists():
        print(
            "Error: test-vectors directory not found. "
            "Please specify --test-vectors or ensure test-vectors is in a standard location."
        )
        return 1

    print(f"Using test-vectors from: {test_vectors}")
    print(f"Creating test data in: {args.output}")

    # Copy sample data
    fixtures_copied = copy_sample_fixtures(test_vectors, args.output, args.max_files)
    contexts_copied = copy_sample_contexts(test_vectors, args.output, args.max_files)

    print(f"\nSummary:")
    print(f"  Fixtures copied: {fixtures_copied}")
    print(f"  Contexts copied: {contexts_copied}")

    if fixtures_copied == 0 and contexts_copied == 0:
        print("\nWarning: No test data was copied!")
        return 1

    print(f"\nTest data ready in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
