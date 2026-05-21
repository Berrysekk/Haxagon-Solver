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
    """Single scrambled QR image split into 3x3 grid — try all 9! permutations."""
    from PIL import Image
    import io, itertools, tempfile, os
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    w, h = img.size
    pw, ph = w // 3, h // 3
    # Extract the 9 tiles
    tiles = []
    for row in range(3):
        for col in range(3):
            box = (col * pw, row * ph, (col + 1) * pw, (row + 1) * ph)
            tiles.append(img.crop(box))
    # Try all permutations, scan each assembled image for a QR code
    for perm in itertools.permutations(range(9)):
        canvas = Image.new("RGB", (w, h))
        for idx, tile_idx in enumerate(perm):
            col, row = idx % 3, idx // 3
            canvas.paste(tiles[tile_idx], (col * pw, row * ph))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            canvas.save(f.name)
            result = scan_qr(f.name)
            os.unlink(f.name)
        if result:
            match = re.search(r'haxagon\{[^}]+\}', result)
            return match.group(0) if match else result
    return None


@register("log4forensic")
def log4forensic(ctx: dict) -> str | None:
    """PCAP with Log4Shell JNDI — flag is base64-encoded across adjacent LDAP response chunks."""
    import base64, subprocess, tempfile, os
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    strs = subprocess.run(["strings", "-4", tmp], capture_output=True, text=True).stdout.splitlines()
    os.unlink(tmp)

    # Direct flag check
    for s in strs:
        m = re.search(r'haxagon\{[^}]+\}', s)
        if m:
            return m.group(0)

    # Collect base64 candidates — strip non-b64 edge chars, keep strings ≥8 b64 chars
    b64_chars = re.compile(r'^[A-Za-z0-9+/=]{8,}$')
    b64_candidates = []
    for s in strs:
        cleaned = re.sub(r'^[^A-Za-z0-9+/=]+|[^A-Za-z0-9+/=]+$', '', s)
        if b64_chars.match(cleaned):
            b64_candidates.append(cleaned)
    # Try singles, pairs, and triples of consecutive candidates
    for i in range(len(b64_candidates)):
        for length in (1, 2, 3):
            chunk = "".join(b64_candidates[i:i + length])
            padded = chunk + "=" * ((-len(chunk)) % 4)
            try:
                decoded = base64.b64decode(padded, validate=False).decode("utf-8", errors="replace")
                m = re.search(r'haxagon\{[^}]+\}', decoded)
                if m:
                    return m.group(0)
            except Exception:
                pass
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
            return f"haxagon{{{candidate}}}"
    return None


@register("someone-cooked-here")
def someone_cooked_here(ctx: dict) -> str | None:
    """Reverse image search for location — requires manual work."""
    return None


@register("lan-party")
async def lan_party(ctx: dict) -> str | None:
    """Container challenge: start, get PCAP from container, extract flag from plaintext traffic."""
    import re as _re
    page = ctx["page"]

    # --- start container if not running ---
    body = await page.inner_text('body')
    if 'running' not in body.lower():
        btn = await page.query_selector('button:has-text("Start"), button:has-text("Connect")')
        if btn and await btn.is_enabled():
            await btn.click()
            await page.wait_for_timeout(10000)
            body = await page.inner_text('body')

    # --- try to extract container IP from page ---
    ip_match = _re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)', body)
    container_ip = ip_match.group(1) if ip_match else None

    # --- collect any static file links from ctx ---
    all_urls = list(ctx.get("files", []))

    # --- if container IP available, try well-known PCAP paths ---
    if container_ip:
        for path in ["/traffic.pcap", "/lan.pcap", "/capture.pcap", "/party.pcap", "/challenge.pcap", "/flag.pcap"]:
            all_urls.append(f"http://{container_ip}{path}")

    for url in all_urls:
        try:
            resp = requests.get(url, timeout=20)
            if len(resp.content) < 10:
                continue
            # Check raw bytes for flag first
            raw = resp.content.decode('latin-1', errors='replace')
            m = _re.search(r'haxagon\{[^}]+\}', raw)
            if m:
                return m.group(0)
            # Write to temp and run strings
            with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
                f.write(resp.content)
                tmp = f.name
            try:
                strs = strings_extract(tmp, min_length=4)
                for s in strs:
                    match = _re.search(r'haxagon\{[^}]+\}', s)
                    if match:
                        return match.group(0)
            finally:
                os.unlink(tmp)
        except Exception:
            continue

    # --- fallback: check links visible on the page ---
    hrefs = await page.eval_on_selector_all('a[href]', 'els => els.map(e => e.href)')
    for href in hrefs:
        if any(ext in href for ext in ['.pcap', '/download', '/files', 'static.haxagon']):
            if href not in all_urls:
                try:
                    resp = requests.get(href, timeout=20)
                    raw = resp.content.decode('latin-1', errors='replace')
                    m = _re.search(r'haxagon\{[^}]+\}', raw)
                    if m:
                        return m.group(0)
                    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=False) as f:
                        f.write(resp.content)
                        tmp = f.name
                    try:
                        strs = strings_extract(tmp, min_length=4)
                        for s in strs:
                            match = _re.search(r'haxagon\{[^}]+\}', s)
                            if match:
                                return match.group(0)
                    finally:
                        os.unlink(tmp)
                except Exception:
                    continue
    return None
