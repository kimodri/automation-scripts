# Number CamScanner Files

`number_files_cam_scanner.py` renames CamScanner-style files by reading the number at the end of each original filename. It applies a chosen starting offset, produces a zero-padded name, and preserves the file extension.

This is useful when scanned pages already have ordered names such as `scan_1.pdf`, `scan_2.pdf`, and `scan_3.pdf`, but their final numbering needs to begin at a different value.

## Requirements

- Python 3
- No third-party packages

## Usage

Run the command from the repository root:

```text
python scripts/number_files_cam_scanner.py <directory> --start_number <number>
```

Arguments:

- `<directory>` is the path to the folder containing the CamScanner files.
- `--start_number` is optional and sets the new number for the file whose original suffix is `_1`. It defaults to `0`.

For example:

```text
python scripts/number_files_cam_scanner.py "C:\path\to\scans" --start_number 12
```

The script calculates each new number as `start_number + original suffix - 1`:

```text
scan_1.pdf -> 0012.pdf
scan_2.pdf -> 0013.pdf
scan_3.pdf -> 0014.pdf
```

To use the default starting number, omit the option:

```text
python scripts/number_files_cam_scanner.py "C:\path\to\scans"
```

## Filename Format

The original filename must end with an underscore followed by a number and an extension:

```text
document_1.pdf
page_25.jpg
scan_103.png
```

Files that do not match this format are left unchanged.

## Current Behavior and Limitations

- The script processes only files directly inside the selected directory. It skips subdirectories.
- The final sequence is based on the numeric suffix in each filename rather than filesystem order.
- Existing files with the intended destination names can cause filename collisions and stop the script.
- The current padding logic supports calculated numbers below `1000`; values at or above `1000` are not handled correctly.
- The original filename is discarded apart from its extension and trailing sequence number.
- Renaming changes the original files immediately and does not include an undo operation. Test the command on copied files or back up the directory first.

[Back to the script list](../../README.md)
