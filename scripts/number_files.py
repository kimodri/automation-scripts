import argparse
from pathlib import Path
import os

def number_files(directory: str, start_no: int):
    
    # Resolve the path
    path = directory
    path = Path(path).resolve()

    if not path.exists() or not path.is_dir():
        raise ValueError(f"Invalid folder path: {path}")

    for idx, file in enumerate(list(path.iterdir())):
        
        if file.is_file():
            if start_no < 10:
                new_name = f"0{start_no + idx}{file.suffix}"
                new_file = file.with_name(new_name)
                file.rename(new_file)
                print(f"Renamed: {file} to {new_file.name}")
        elif file.is_dir():
            print(f"Skipped: {file} is directory.")
        
    
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