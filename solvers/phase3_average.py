import re
import hashlib
import requests
import tempfile
import os
from registry import register
from tools.image_utils import scan_qr
from tools.stego import strings_extract


@register("qr-struggle")
def qr_struggle(ctx: dict) -> str | None:
    """Reassemble fragmented QR code pieces and decode."""
    from PIL import Image
    import io
    if len(ctx["files"]) < 2:
        return None
    pieces = []
    for url in ctx["files"]:
        resp = requests.get(url, timeout=30)
        pieces.append(Image.open(io.BytesIO(resp.content)))
    total_w = sum(p.width for p in pieces)
    assembled = Image.new("RGB", (total_w, max(p.height for p in pieces)))
    x = 0
    for p in pieces:
        assembled.paste(p, (x, 0))
        x += p.width
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        assembled.save(f.name)
        result = scan_qr(f.name)
        os.unlink(f.name)
    if result:
        match = re.search(r'CTF\{[^}]+\}', result)
        return match.group(0) if match else result
    return None


@register("log4forensic")
def log4forensic(ctx: dict) -> str | None:
    """Grep Log4j logs for flag or JNDI payload."""
    if not ctx["files"]:
        return None
    log_content = requests.get(ctx["files"][0], timeout=30).text
    match = re.search(r'CTF\{[^}]+\}', log_content)
    if match:
        return match.group(0)
    jndi = re.findall(r'\$\{jndi:ldap://[^}]+\}', log_content)
    if jndi:
        decoded = re.search(r'ldap://[^/]+/([^}]+)', jndi[-1])
        if decoded:
            return f"CTF{{{decoded.group(1)}}}"
    return None


@register("blessed-sha-512")
def blessed_sha512(ctx: dict) -> str | None:
    """Brute-force short hash against wordlist."""
    target_hash = re.search(r'\b[0-9a-fA-F]{128}\b', ctx["description"])
    if not target_hash:
        return None
    target = target_hash.group(0).lower()
    candidates = (
        [str(i) for i in range(10000)] +
        ["password", "flag", "secret", "admin", "root", "haxagon"]
    )
    for candidate in candidates:
        if hashlib.sha512(candidate.encode()).hexdigest() == target:
            return f"CTF{{{candidate}}}"
    return None


@register("someone-cooked-here")
def someone_cooked_here(ctx: dict) -> str | None:
    """Reverse image search for location — requires manual work."""
    return None


@register("lan-party")
def lan_party(ctx: dict) -> str | None:
    """Wireshark PCAP — extract flag from plaintext traffic."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    strs = strings_extract(tmp, min_length=4)
    os.unlink(tmp)
    for s in strs:
        match = re.search(r'CTF\{[^}]+\}', s)
        if match:
            return match.group(0)
    return None
