# solvers/phase1_simple.py
"""
Phase 1 Simple challenge solvers.
Each solver receives ctx = {'description': str, 'files': [url,...], 'page': Playwright Page}
and returns a flag string or None.
"""
import re
import requests
from registry import register


@register("level0")
def level0(ctx: dict) -> str | None:
    """Tutorial — flag is shown directly on the page."""
    match = re.search(r'CTF\{[^}]+\}', ctx["description"])
    return match.group(0) if match else None


@register("create-secure-password")
def create_secure_password(ctx: dict) -> str | None:
    """Flag is revealed after submitting any strong password."""
    return None  # handled by manual interaction fallback


@register("what-is-my-ip")
def what_is_my_ip(ctx: dict) -> str | None:
    """Flag format: CTF{<your public IP>}"""
    ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
    return f"CTF{{{ip}}}"


@register("terms-of-service")
def terms_of_service(ctx: dict) -> str | None:
    """Flag hidden in ToS text."""
    match = re.search(r'CTF\{[^}]+\}', ctx["description"], re.IGNORECASE)
    return match.group(0) if match else None


@register("enhance")
async def enhance(ctx: dict) -> str | None:
    """Brighten image, then OCR for flag."""
    import tempfile
    import os
    from tools.image_utils import brighten, extract_text_from_image
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    brightened = brighten(tmp)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
        f2.write(brightened)
        bright_path = f2.name
    text = extract_text_from_image(bright_path)
    os.unlink(tmp)
    os.unlink(bright_path)
    match = re.search(r'CTF\{[^}]+\}', text)
    return match.group(0) if match else None


@register("crime-scene")
def crime_scene(ctx: dict) -> str | None:
    """Flag in description text."""
    match = re.search(r'CTF\{[^}]+\}', ctx["description"])
    return match.group(0) if match else None


@register("html-maze")
async def html_maze(ctx: dict) -> str | None:
    """Flag hidden in page HTML/source."""
    content = await ctx["page"].content()
    match = re.search(r'CTF\{[^}]+\}', content)
    return match.group(0) if match else None


@register("nokia-incident")
def nokia_incident(ctx: dict) -> str | None:
    """T9 multi-tap decoding."""
    digits = re.findall(r'\d+', ctx["description"])
    if not digits:
        return None
    t9_map = {
        '2': 'A', '22': 'B', '222': 'C',
        '3': 'D', '33': 'E', '333': 'F',
        '4': 'G', '44': 'H', '444': 'I',
        '5': 'J', '55': 'K', '555': 'L',
        '6': 'M', '66': 'N', '666': 'O',
        '7': 'P', '77': 'Q', '777': 'R', '7777': 'S',
        '8': 'T', '88': 'U', '888': 'V',
        '9': 'W', '99': 'X', '999': 'Y', '9999': 'Z',
        '0': ' ',
    }
    raw = ''.join(digits)
    decoded = []
    i = 0
    while i < len(raw):
        d = raw[i]
        count = 1
        while i + count < len(raw) and raw[i + count] == d:
            count += 1
        decoded.append(t9_map.get(d * count, '?'))
        i += count
    result = ''.join(decoded)
    match = re.search(r'CTF\{[^}]+\}', result, re.IGNORECASE)
    if match:
        return match.group(0)
    return f"CTF{{{result}}}" if result.strip() else None


@register("break-me")
async def break_me(ctx: dict) -> str | None:
    """Try basic XSS or SQLi payloads."""
    page = ctx["page"]
    payloads = ["' OR '1'='1", "admin'--", "<script>alert(1)</script>"]
    for payload in payloads:
        inputs = await page.query_selector_all('input[type="text"], input:not([type])')
        for inp in inputs:
            await inp.fill(payload)
        submit = await page.query_selector('button[type="submit"]')
        if submit:
            await submit.click()
            await page.wait_for_load_state("networkidle")
        match = re.search(r'CTF\{[^}]+\}', await page.content())
        if match:
            return match.group(0)
    return None
