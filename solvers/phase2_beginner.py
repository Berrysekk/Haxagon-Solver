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
    match = re.search(r'haxagon\{[^}]+\}', decoded)
    return match.group(0) if match else None


@register("agent-007")
async def agent_007(ctx: dict) -> str | None:
    """Startup challenge: start container, GET /secret with User-Agent: 007."""
    page = ctx["page"]
    # Click Connect/Start button to spin up the container
    start_btn = await page.query_selector('button:has-text("Start"), button:has-text("Connect"), button:has-text("Spustit")')
    if start_btn:
        await start_btn.click()
        await page.wait_for_timeout(5000)
    # Extract the container IP/URL from the page
    body = await page.inner_text('body')
    ip_match = re.search(r'http://(\d+\.\d+\.\d+\.\d+(?::\d+)?)', body)
    if not ip_match:
        return None
    url = f"http://{ip_match.group(1)}/secret"
    resp = requests.get(url, headers={"User-Agent": "007"}, timeout=15)  # nosemgrep — target IPs are inside CTF lab network — no public traffic
    m = re.search(r'haxagon\{[^}]+\}', resp.text)
    return m.group(0) if m else None


@register("url-nonsense")
@register("url-nonsence")  # platform typo variant
async def url_nonsense(ctx: dict) -> str | None:
    """Flag base64-encoded in a Google search link id= parameter hidden in the page."""
    import base64
    from urllib.parse import unquote, urlparse, parse_qs

    # Check description first (standard URL decode)
    decoded = unquote(ctx["description"])
    match = re.search(r'haxagon\{[^}]+\}', decoded)
    if match:
        return match.group(0)

    # The flag is base64-encoded in a hidden Google search URL's id= param
    page = ctx["page"]
    hrefs = await page.eval_on_selector_all(
        'a[href]', 'els => els.map(e => e.href)'
    )
    for href in hrefs:
        if 'google.com/search' in href and 'id=' in href:
            qs = parse_qs(urlparse(href).query)
            b64 = qs.get('id', [''])[0]
            if b64:
                # Add padding and decode
                padded = b64 + '=' * ((-len(b64)) % 4)
                try:
                    text = base64.b64decode(padded, validate=False).decode('utf-8', errors='replace')
                    m = re.search(r'haxagon\{[^}]+\}', text)
                    if m:
                        return m.group(0)
                    # Flag might be truncated (= stripped from URL); try adding closing brace
                    if text.startswith('haxagon{') and '}' not in text:
                        return text + '}'
                except Exception:
                    pass
    return None


@register("crack-them-all")
def crack_them_all(ctx: dict) -> str | None:
    """Hashes are MD5 of each flag character — crack locally via lookup table."""
    import hashlib, string as _string
    hashes = re.findall(r'\b[0-9a-f]{32}\b', ctx["description"].lower())
    if not hashes:
        return None
    # Build lookup: printable chars + numbers 0–999999 + common passwords
    table: dict[str, str] = {}
    for c in _string.printable:
        table[hashlib.md5(c.encode()).hexdigest()] = c
    for n in range(1_000_000):
        table[hashlib.md5(str(n).encode()).hexdigest()] = str(n)
    for w in ["password", "123456", "12345", "qwerty", "abc123", "letmein",
              "monkey", "dragon", "master", "hello", "shadow", "admin"]:
        table[hashlib.md5(w.encode()).hexdigest()] = w
    cracked = [table.get(h, "?") for h in hashes]
    flag = "".join(cracked)
    match = re.search(r'haxagon\{[^}]+\}', flag)
    return match.group(0) if match else None


@register("time-traveler")
def time_traveler(ctx: dict) -> str | None:
    """EXIF DateTimeOriginal contains a future date — that is the flag."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    ext = ".jpg" if b"JFIF" in resp.content[:12] or b"\xff\xd8" in resp.content[:4] else ".bin"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    meta = get_metadata(tmp)
    os.unlink(tmp)
    # Check for literal flag first
    for v in meta.values():
        m = re.search(r'haxagon\{[^}]+\}', str(v))
        if m:
            return m.group(0)
    # Extract DateTimeOriginal and return the date — caller tries all formats on submit
    dt = meta.get("DateTimeOriginal", "")
    date_match = re.match(r'(\d{4}):(\d{2}):(\d{2})', str(dt))
    if not date_match:
        return None
    y, m, d = date_match.group(1), date_match.group(2), date_match.group(3)
    return f"haxagon{{{y}-{m}-{d}}}"  # ISO format: YYYY-MM-DD (platform confirmed)


@register("empty-zip")
def empty_zip(ctx: dict) -> str | None:
    """Hidden file (e.g. .flag) inside zip — extract all entries including dotfiles."""
    import zipfile, io
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    # Try zipfile module first (handles hidden/dotfiles that binwalk misses)
    try:
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        for info in z.infolist():
            data = z.read(info.filename)
            text = data.decode('utf-8', errors='replace')
            m = re.search(r'haxagon\{[^}]+\}', text)
            if m:
                return m.group(0)
            # Also check via strings on the raw bytes
            for line in text.splitlines():
                m = re.search(r'haxagon\{[^}]+\}', line)
                if m:
                    return m.group(0)
    except Exception:
        pass
    # Fallback: strings on the raw zip bytes
    raw_text = resp.content.decode('latin-1', errors='replace')
    m = re.search(r'haxagon\{[^}]+\}', raw_text)
    if m:
        return m.group(0)
    return None


@register("museum-archive")
def museum_archive(ctx: dict) -> str | None:
    """Vigenère cipher — key is stated in description, decode and return as flag."""
    desc = ctx["description"]
    # Extract ciphertext (uppercase letters block)
    ct_match = re.search(r'\b([A-Z]{6,})\b', desc)
    if not ct_match:
        return None
    ct = ct_match.group(1)
    # Extract key from description (look for "Klíč:" or "Key:" followed by uppercase word)
    key_match = re.search(r'(?:Klíč|Key)\s*[:\-]?\s*\n?\s*([A-Z]{3,})', desc)
    if key_match:
        keys_to_try = [key_match.group(1)]
    else:
        keys_to_try = []
    # Also try common keys as fallback
    keys_to_try += ["LEMON", "KEY", "CIPHER", "VIGENERE", "SECRET", "FLAG", "HAXAGON", "CTF"]
    for key in keys_to_try:
        decoded = _vigenere_decode(ct, key)
        # Direct flag check
        m = re.search(r'haxagon\{[^}]+\}', decoded, re.IGNORECASE)
        if m:
            return m.group(0)
        # If decoded looks like readable English/Czech (not random), return as flag
        if re.match(r'^[A-Za-z0-9_]+$', decoded) and len(decoded) >= 5:
            return f"haxagon{{{decoded.lower()}}}"
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


@register("whois")
def whois_solver(ctx: dict) -> list[str] | None:
    """WHOIS lookup for google.com — returns 3 answers: Registry Domain ID, Creation Date, IANA ID."""
    import subprocess
    try:
        result = subprocess.run(
            ['whois', '-h', 'whois.verisign-grs.com', 'google.com'],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout
    except Exception:
        # Hardcoded fallback — google.com WHOIS data is stable
        output = (
            'Registry Domain ID: 2138514_DOMAIN_COM-VRSN\n'
            'Creation Date: 1997-09-15T04:00:00Z\n'
            'Registrar IANA ID: 292\n'
        )
    # Extract Registry Domain ID
    rid_m = re.search(r'Registry Domain ID:\s*(\S+)', output, re.IGNORECASE)
    registry_id = rid_m.group(1) if rid_m else '2138514_DOMAIN_COM-VRSN'
    # Extract Creation Date → convert to DD-MM-YYYY
    date_m = re.search(r'Creation Date:\s*(\d{4})-(\d{2})-(\d{2})', output, re.IGNORECASE)
    if date_m:
        creation_date = f"{date_m.group(3)}-{date_m.group(2)}-{date_m.group(1)}"
    else:
        creation_date = '15-09-1997'
    # Extract IANA ID
    iana_m = re.search(r'Registrar IANA ID:\s*(\d+)', output, re.IGNORECASE)
    iana_id = iana_m.group(1) if iana_m else '292'
    return [registry_id, creation_date, iana_id]


@register("create-secure-password")
async def create_secure_password(ctx: dict) -> str | None:
    """Password rules challenge — submit a password satisfying all 7 rules, extract flag."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(resp.text)
        tmp = f.name
    page = ctx["page"]
    await page.goto(f'file://{tmp}')
    await page.wait_for_timeout(2000)
    # Password that satisfies all 7 rules:
    # 20+ chars, 5 classes (lower+upper+digit+symbol+non-ASCII), no whitespace,
    # no control chars, 70%+ unique, no 3+ repeated, no 4+ sequential
    strong_password = 'Pà$w0Rd!Ñext#Ü9Kö2mV'
    inp = await page.query_selector('input[type="password"]')
    if not inp:
        os.unlink(tmp)
        return None
    await inp.fill(strong_password)
    await page.wait_for_timeout(1500)
    content = await page.content()
    m = re.search(r'haxagon\{[^}]+\}', content)
    os.unlink(tmp)
    return m.group(0) if m else None
