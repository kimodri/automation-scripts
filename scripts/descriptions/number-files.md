# Number Files

`number_files.py` renames files in a directory with sequential, zero-padded numbers. It preserves each file's extension and replaces the rest of the filename.

This is useful when a folder contains files that need simple numeric names, such as pages, images, or documents that will be processed in sequence.

## Requirements

- Python 3
- No third-party packages

## Usage

Run the command from the repository root:

```text
python scripts/number_files.py <directory> --start_number <number>
```

Arguments:

- `<directory>` is the path to the folder containing the files to rename.
- `--start_number` is optional and sets the first number used. It defaults to `0`.

For example:

```text
python scripts/number_files.py "C:\path\to\documents" --start_number 1
```

Given a folder containing three PDF files, the script renames them using the sequence it receives from the filesystem:

```text
first-document.pdf  -> 0001.pdf
second-document.pdf -> 0002.pdf
third-document.pdf  -> 0003.pdf
```

To use the default starting number, omit the option:

```text
python scripts/number_files.py "C:\path\to\documents"
```

## Current Behavior and Limitations

- The script processes only files directly inside the selected directory. It skips subdirectories.
- File order comes from the filesystem and is not explicitly sorted. Confirm the resulting order is suitable before relying on it.
- Subdirectories still occupy positions in the directory sequence, so they can cause gaps in the assigned file numbers.
- Existing files with the intended destination names can cause filename collisions and stop the script.
- The current padding logic is designed around starting numbers below `1000` and can become inconsistent when a sequence crosses a digit boundary.
- Renaming changes the original files immediately and does not include an undo operation. Test the command on copied files or back up the directory first.

[Back to the script list](../../README.md)
