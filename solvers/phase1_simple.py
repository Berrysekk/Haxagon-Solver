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
    match = re.search(r'haxagon\{[^}]+\}', ctx["description"])
    return match.group(0) if match else None


@register("create-secure-password")
def create_secure_password(ctx: dict) -> str | None:
    """Flag is revealed after submitting any strong password."""
    return None  # handled by manual interaction fallback


@register("what-is-my-ip")
async def what_is_my_ip(ctx: dict) -> str | None:
    """Start container, POST public IP to /api/check-ip, return flag."""
    import re as _re
    page = ctx["page"]
    body = await page.inner_text('body')
    # Click Start if container not running
    if 'running' not in body:
        start_btn = await page.query_selector('button:has-text("Start")')
        if start_btn and await start_btn.is_enabled():
            await start_btn.click()
            await page.wait_for_timeout(8000)
            body = await page.inner_text('body')
    # Extract container IP
    ip_match = _re.search(r'Ip:\s*\n?\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)', body)
    if not ip_match:
        ip_match = _re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)', body)
    if not ip_match:
        return None
    container_ip = ip_match.group(1)
    # Get public IP and submit to container
    try:
        public_ip = requests.get('https://api.ipify.org', timeout=10).text.strip()
        resp = requests.post(f'http://{container_ip}/api/check-ip', json={'ip': public_ip}, timeout=15)  # nosemgrep — target IPs are inside CTF lab network — no public traffic
        m = _re.search(r'haxagon\{[^}]+\}', resp.text)
        return m.group(0) if m else None
    except Exception:
        return None


@register("terms-of-service")
def terms_of_service(ctx: dict) -> str | None:
    """Flag hidden inside the Terms of Service HTML file."""
    # Check description first
    match = re.search(r'haxagon\{[^}]+\}', ctx["description"], re.IGNORECASE)
    if match:
        return match.group(0)
    # Flag is buried in the ToS HTML file
    for url in ctx["files"]:
        try:
            resp = requests.get(url, timeout=30)
            match = re.search(r'haxagon\{[^}]+\}', resp.text, re.IGNORECASE)
            if match:
                return match.group(0)
        except Exception:
            pass
    return None


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
    match = re.search(r'haxagon\{[^}]+\}', text)
    return match.group(0) if match else None


@register("crime-scene")
def crime_scene(ctx: dict) -> str | None:
    """Boustrophedon-encoded letter from Moriarty — find the next victim's name."""
    desc = ctx["description"]
    # Direct flag check
    match = re.search(r'haxagon\{[^}]+\}', desc)
    if match:
        return match.group(0)
    # Extract grid: lines of all-uppercase letters, 6+ chars
    grid_rows = re.findall(r'^[A-Z]{6,}$', desc, re.MULTILINE)
    if not grid_rows:
        return None
    # Decode boustrophedon (alternating left→right, right→left)
    decoded_chars = []
    for i, row in enumerate(grid_rows):
        decoded_chars.extend(row if i % 2 == 0 else reversed(row))
    text = ''.join(decoded_chars)
    # Check for direct flag in decoded text
    m = re.search(r'haxagon\{[^}]+\}', text, re.IGNORECASE)
    if m:
        return m.group(0)
    # Find victim name after "VICTIMIS"
    if 'VICTIMIS' not in text:
        return None
    after = text[text.find('VICTIMIS') + 8:]
    # Name ends before the article "A" that starts a descriptor phrase
    # Pattern: name ends where we hit A + consonant start of English adj/noun
    name_m = re.match(r'([A-Z]+?)(?=AQUIET|AWHO|AWAS|ANICE|AYOUNG|ASMALL|ABIG|THE|WHO|AND)', after)
    if not name_m:
        # Fallback: try common first names to split
        FIRST_NAMES = ['PETER', 'JOHN', 'JAMES', 'DAVID', 'MICHAEL', 'PAUL', 'MARK',
                       'JANE', 'MARY', 'ALICE', 'EMMA', 'ANNA', 'SARAH', 'JACK', 'ADAM',
                       'ALEX', 'MATT', 'CHRIS', 'ROBERT', 'WILLIAM', 'RICHARD', 'THOMAS',
                       'GEORGE', 'HENRY', 'OLIVER', 'LUCAS', 'ETHAN', 'RYAN', 'NOAH',
                       'LIAM', 'ANDREW', 'DANIEL', 'MARTIN', 'SIMON', 'VICTOR']
        for fname in sorted(FIRST_NAMES, key=len, reverse=True):
            if after.startswith(fname):
                rest = after[len(fname):]
                # Extract last name: stop at stop-word
                lname_m = re.match(r'([A-Z]{2,15})(?=[A-Z]{1}(?:QUIET|WHO|THE|AND|WAS|IS[A-Z])|$)', rest)
                if not lname_m:
                    lname_m = re.match(r'([A-Z]{2,15})', rest)
                if lname_m:
                    # Trim last name at known English article/word patterns
                    lname = lname_m.group(1)
                    for stop in ['AQUIET', 'AWHO', 'ANICE', 'AYOUNG']:
                        if stop in lname:
                            lname = lname[:lname.find(stop)]
                    return f"haxagon{{{fname.lower()}_{lname.lower()}}}"
        return None
    name_raw = name_m.group(1)
    # Split CamelCase-like name into first/last using FIRST_NAMES list
    FIRST_NAMES = ['PETER', 'JOHN', 'JAMES', 'DAVID', 'MICHAEL', 'PAUL', 'MARK',
                   'JANE', 'MARY', 'ALICE', 'EMMA', 'ANNA', 'SARAH', 'JACK', 'ADAM',
                   'ALEX', 'MATT', 'CHRIS', 'ROBERT', 'WILLIAM', 'RICHARD', 'THOMAS',
                   'GEORGE', 'HENRY', 'OLIVER', 'LUCAS', 'ETHAN', 'RYAN', 'NOAH',
                   'LIAM', 'ANDREW', 'DANIEL', 'MARTIN', 'SIMON', 'VICTOR']
    for fname in sorted(FIRST_NAMES, key=len, reverse=True):
        if name_raw.startswith(fname) and len(name_raw) > len(fname):
            lname = name_raw[len(fname):]
            return f"haxagon{{{fname.lower()}_{lname.lower()}}}"
    return f"haxagon{{{name_raw.lower()}}}"


@register("html-maze")
async def html_maze(ctx: dict) -> str | None:
    """Hash-based SPA maze — BFS through all '#/...' routes to find the flag."""
    import tempfile, os
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='wb') as f:
        f.write(resp.content)
        tmp = f.name
    page = ctx["page"]
    base_url = f'file://{tmp}'
    visited: set[str] = set()
    to_visit = ['#/', '#/0', '#/1', '#/2']
    found_flag = None
    try:
        while to_visit and not found_flag:
            hash_path = to_visit.pop(0)
            if hash_path in visited:
                continue
            visited.add(hash_path)
            if len(visited) > 2000:  # safety limit
                break
            await page.goto(base_url + hash_path)
            await page.wait_for_timeout(300)
            content = await page.content()
            m = re.search(r'haxagon\{[^}]+\}', content)
            if m:
                found_flag = m.group(0)
                break
            links = await page.eval_on_selector_all(
                'a[href]', 'els => els.map(e => e.getAttribute("href"))'
            )
            for link in links:
                if link and link.startswith('#') and link not in visited:
                    to_visit.append(link)
    finally:
        os.unlink(tmp)
    return found_flag


@register("nokia-incident")
def nokia_incident(ctx: dict) -> str | None:
    """T9 multi-tap decoding — keypresses are dash-separated groups."""
    # Find the keypress record: a sequence of digit groups separated by dashes (≥4 groups)
    keypress_line = re.search(r'\d+(?:-\d+){3,}', ctx["description"])
    if not keypress_line:
        return None
    t9_map = {
        '2': 'a', '22': 'b', '222': 'c',
        '3': 'd', '33': 'e', '333': 'f',
        '4': 'g', '44': 'h', '444': 'i',
        '5': 'j', '55': 'k', '555': 'l',
        '6': 'm', '66': 'n', '666': 'o',
        '7': 'p', '77': 'q', '777': 'r', '7777': 's',
        '8': 't', '88': 'u', '888': 'v',
        '9': 'w', '99': 'x', '999': 'y', '9999': 'z',
        '0': ' ',
    }
    groups = keypress_line.group(0).split('-')
    decoded = ''.join(t9_map.get(g, '?') for g in groups)
    result = decoded.replace(' ', '')
    return f"haxagon{{{result}}}" if result.strip('?') else None


@register("break-me")
async def break_me(ctx: dict) -> str | None:
    """Math Checker with obfuscated JS — submitting 'true' breaks loose type comparison."""
    if not ctx["files"]:
        return None
    # Download and open the HTML file locally
    resp = requests.get(ctx["files"][0], timeout=30)
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="wb") as f:
        f.write(resp.content)
        tmp = f.name
    page = ctx["page"]
    await page.goto(f"file://{tmp}")
    await page.wait_for_timeout(2000)
    # 'true' coerces to truthy in loose JS == comparison, breaking the validator
    for payload in ["true", "1==1", "1"]:
        inp = await page.query_selector("input")
        if not inp:
            break
        await inp.fill(payload)
        btn = await page.query_selector("button")
        if btn:
            await btn.click()
            await page.wait_for_timeout(500)
        match = re.search(r'haxagon\{[^}]+\}', await page.content())
        if match:
            os.unlink(tmp)
            return match.group(0)
    os.unlink(tmp)
    return None
