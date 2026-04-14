import subprocess
import tempfile
import os

def binwalk_extract(filepath: str) -> list[str]:
    """Run binwalk -e on file, return list of extracted file paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["binwalk", "-e", "--directory", tmpdir, filepath],
            capture_output=True
        )
        extracted = []
        for root, _, files in os.walk(tmpdir):
            for f in files:
                extracted.append(os.path.join(root, f))
        return extracted

def strings_extract(filepath: str, min_length: int = 6) -> list[str]:
    """Extract printable strings from binary file."""
    result = subprocess.run(
        ["strings", f"-{min_length}", filepath],
        capture_output=True, text=True
    )
    return result.stdout.splitlines()
