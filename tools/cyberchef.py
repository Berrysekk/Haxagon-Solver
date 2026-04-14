import subprocess
import json
import tempfile
import os
import base64
from urllib.parse import unquote

def run_recipe(recipe: list[dict], input_data: str) -> str:
    """
    Run a CyberChef recipe via the cyberchef-cli Node package.
    Falls back to pure-Python for common ops if CLI unavailable.
    """
    try:
        recipe_json = json.dumps({"recipe": recipe})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(recipe_json)
            recipe_path = f.name
        result = subprocess.run(
            ["cyberchef-cli", "--recipe", recipe_path, "--input", input_data],
            capture_output=True, text=True, timeout=15
        )
        os.unlink(recipe_path)
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if len(recipe) == 1:
        op = recipe[0]["op"].lower()
        if op == "from hex":
            return bytes.fromhex(input_data.replace(" ", "")).decode(errors="replace")
        if op == "url decode":
            return unquote(input_data)
        if op == "from base64":
            return base64.b64decode(input_data).decode(errors="replace")
        if op == "rot13":
            return input_data.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))
    return input_data
