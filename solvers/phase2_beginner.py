import re
import requests
import tempfile
import os
from registry import register
from tools.cyberchef import run_recipe
from tools.exiftool import get_metadata
from tools.stego import binwalk_extract, strings_extract
from tools.crackstation import crack_hash


@register("0-f")
def hex_decode(ctx: dict) -> str | None:
    """Hex-encoded flag."""
    hex_str = re.search(r'[0-9a-fA-F]{10,}', ctx["description"])
    if not hex_str:
        return None
    decoded = run_recipe([{"op": "From Hex", "args": []}], hex_str.group(0))
    match = re.search(r'CTF\{[^}]+\}', decoded)
    return match.group(0) if match else None


@register("agent-007")
async def agent_007(ctx: dict) -> str | None:
    """Change User-Agent header to '007'."""
    page = ctx["page"]
    await page.set_extra_http_headers({"User-Agent": "007"})
    await page.reload()
    await page.wait_for_load_state("networkidle")
    match = re.search(r'CTF\{[^}]+\}', await page.content())
    return match.group(0) if match else None


@register("url-nonsense")
def url_nonsense(ctx: dict) -> str | None:
    """URL-encoded flag in description."""
    from urllib.parse import unquote
    decoded = unquote(ctx["description"])
    match = re.search(r'CTF\{[^}]+\}', decoded)
    return match.group(0) if match else None


@register("crack-them-all")
def crack_them_all(ctx: dict) -> str | None:
    """Multiple hashes to crack."""
    hashes = re.findall(r'\b[0-9a-fA-F]{32,128}\b', ctx["description"])
    results = []
    for h in hashes:
        cracked = crack_hash(h)
        if cracked:
            results.append(cracked)
    if not results:
        return None
    candidate = ''.join(results)
    match = re.search(r'CTF\{[^}]+\}', candidate)
    return match.group(0) if match else f"CTF{{{candidate}}}"


@register("time-traveler")
def time_traveler(ctx: dict) -> str | None:
    """EXIF metadata contains flag."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    meta = get_metadata(tmp)
    os.unlink(tmp)
    for v in meta.values():
        match = re.search(r'CTF\{[^}]+\}', str(v))
        if match:
            return match.group(0)
    return None


@register("empty-zip")
def empty_zip(ctx: dict) -> str | None:
    """Hidden file inside zip via binwalk."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    extracted = binwalk_extract(tmp)
    os.unlink(tmp)
    for filepath in extracted:
        for s in strings_extract(filepath):
            if "CTF{" in s:
                match = re.search(r'CTF\{[^}]+\}', s)
                if match:
                    return match.group(0)
    return None


@register("museum-archive")
def museum_archive(ctx: dict) -> str | None:
    """Vigenère cipher — try common keys."""
    ciphertext = re.search(r'[A-Z]{10,}', ctx["description"])
    if not ciphertext:
        return None
    ct = ciphertext.group(0)
    for key in ["KEY", "CIPHER", "VIGENERE", "SECRET", "FLAG", "HAXAGON"]:
        decoded = _vigenere_decode(ct, key)
        if "CTF" in decoded:
            match = re.search(r'CTF\{[^}]+\}', decoded)
            if match:
                return match.group(0)
    return None


def _vigenere_decode(ciphertext: str, key: str) -> str:
    result = []
    key = key.upper()
    ki = 0
    for c in ciphertext:
        if c.isalpha():
            shift = ord(key[ki % len(key)]) - ord('A')
            dec = chr((ord(c.upper()) - ord('A') - shift) % 26 + ord('A'))
            result.append(dec)
            ki += 1
        else:
            result.append(c)
    return ''.join(result)
