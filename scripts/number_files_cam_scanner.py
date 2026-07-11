"""
TODO:
1. Adding 0 padding is brittle and can be improved.
"""

import argparse
from pathlib import Path
import re

suffix_pattern = r"_(\d+)\.[a-zA-Z0-9]+$"

def number_files(directory: str, start_no: int):
    
    # Resolve the path
    path = directory
    path = Path(path).resolve()

    if not path.exists() or not path.is_dir():
        raise ValueError(f"Invalid folder path: {path}")

    for idx, file in enumerate(list(path.iterdir())):
        
        if file.is_file():
            filename = file.name
            match = re.search(suffix_pattern, filename)
            if match:
                number = int(match.group(1))
                new_number = start_no + number - 1
                if new_number < 10:
                    # new_name = re.replace(suffix_pattern, f"000{new_number}{file.suffix}", filename)
                    new_name = f"000{new_number}{file.suffix}"
                    new_file = file.with_name(new_name)
                    file.rename(new_file)

                elif new_number < 100 and new_number >= 10:
                    # new_name = re.replace(suffix_pattern, f"00{new_number}{file.suffix}", filename)
                    new_name = f"00{new_number}{file.suffix}"
                    new_file = file.with_name(new_name)
                    file.rename(new_file)

                elif new_number < 1000 and new_number >= 100:
                    # new_name = re.replace(suffix_pattern, f"0{new_number}{file.suffix}", filename)
                    new_name = f"0{new_number}{file.suffix}"
                    new_file = file.with_name(new_name)
                    file.rename(new_file)
                print(f"Renamed: {file} to {new_file.name}")
        elif file.is_dir():
            print(f"Skipped: {file} is a directory.")
        
    
if (__name__ =="__main__"):
    parser = argparse.ArgumentParser(description="Number files in a directory.")
    parser.add_argument("directory", type=str, help="Directory containing files to number.", nargs="?")
    parser.add_argument("--start_number", type=int, help="Starting number for file numbering.")
    args = parser.parse_args()

    directory = args.directory
    start_number = args.start_number

    if start_number is None:
        start_number = 0

    number_files(directory, start_number)