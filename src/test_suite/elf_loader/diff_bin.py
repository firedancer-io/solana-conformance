import sys
import subprocess


def hexdump(file_path):
    # Run the hexdump command on the file and return the output
    result = subprocess.run(
        ["hexdump", "-C", file_path], capture_output=True, text=True
    )
    return result.stdout


def compare_files(file1, file2, additional_args):
    # Get hex dumps of both files
    dump1 = hexdump(file1)
    dump2 = hexdump(file2)

    # Use the diff command to compare both hex dumps
    diff_process = subprocess.Popen(
        ["diff"] + additional_args + ["-", "-"],
        stdin=subprocess.PIPE,
        text=True,
        stdout=subprocess.PIPE,
    )

    # Send the hex dump outputs to the diff command
    diff_out, diff_err = diff_process.communicate(input=dump1 + "\n" + dump2)

    return diff_out


def main():
    # Check the number of arguments provided
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <file1> <file2> [diff-options]")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    additional_args = sys.argv[3:]  # Any additional args are passed to the diff command

    # Print the differences
    result = compare_files(file1, file2, additional_args)
    print(result)


if __name__ == "__main__":
    main()
