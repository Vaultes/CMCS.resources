import pathlib
import re
from datetime import datetime


def _clean_path(raw):
    """Tidy up a path that was typed, pasted, or dragged into Terminal."""
    raw = raw.strip()
    # Remove surrounding quotes, if any
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        raw = raw[1:-1]
    # Remove the backslashes Terminal adds when you drag in a file
    # (e.g. "My\ File\ \(1\).xlsx" -> "My File (1).xlsx")
    raw = re.sub(r"\\(.)", r"\1", raw)
    return pathlib.Path(raw).expanduser()


def prompt_for_file(label, suffix=None):
    """Ask for a file path until we get one that exists (and has the right extension)."""
    while True:
        path = _clean_path(input(f"{label}: "))
        if not path.is_file():
            print(f"  File not found: {path}")
            print("  Tip: you can drag the file into this window instead of typing the path.")
            continue
        if suffix and path.suffix.lower() != suffix:
            print(f"  Expected a {suffix} file, but got '{path.name}'. Try again.")
            continue
        return path


def prompt_for_date(label):
    """Ask for a date until we get a valid MM/DD/YYYY value."""
    while True:
        raw = input(f"{label} (MM/DD/YYYY): ").strip()
        try:
            datetime.strptime(raw, "%m/%d/%Y")
            return raw
        except ValueError:
            print("  That's not a valid date in MM/DD/YYYY format. Try again.")

def prompt_for_output(default_name):
    """Ask where to save the output. Press Enter to use the default."""
    while True:
        raw = input(f"Output file (press Enter for {default_name} in the current folder): ").strip()
        if raw == "":
            path = pathlib.Path(default_name)
        else:
            path = _clean_path(raw)
            # If they gave a folder, put the default filename inside it
            if path.is_dir():
                path = path / default_name
        if not path.parent.is_dir():
            print(f"  Folder not found: {path.parent}. Try again.")
            continue
        if path.suffix.lower() != ".csv":
            print("  The output file needs to end in .csv. Try again.")
            continue
        if path.exists():
            answer = input(f"  {path.name} already exists. Overwrite it? (y/n): ").strip().lower()
            if answer != "y":
                continue
        return path