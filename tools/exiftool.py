import subprocess
import json

def get_metadata(filepath: str) -> dict:
    """Run exiftool -json on file, return parsed metadata dict."""
    result = subprocess.run(
        ["exiftool", "-json", filepath],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {}
    try:
        data = json.loads(result.stdout)
        return data[0] if data else {}
    except (json.JSONDecodeError, IndexError):
        return {}
