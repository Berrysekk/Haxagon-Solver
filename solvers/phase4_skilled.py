# solvers/phase4_skilled.py
"""Phase 4 Skilled/Expert challenges."""
import re
import io
import zipfile
import requests
import tempfile
import os
from registry import register


@register("backroom")
async def backroom(ctx: dict) -> str | None:
    """Web exploitation — requires manual analysis."""
    return None


@register("keylogger")
def keylogger(ctx: dict) -> str | None:
    """Malware analysis — requires manual work."""
    return None


@register("journey-around-the-world")
def journey_world(ctx: dict) -> str | None:
    """GeoOSINT — requires human judgment."""
    return None


@register("stein-files")
def stein_files(ctx: dict) -> str | None:
    """Censored PDF — extract text hidden under black rectangles using PyMuPDF."""
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=30)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    try:
        import fitz  # pymupdf
        doc = fitz.open(tmp)
        for page in doc:
            text = page.get_text()
            # Direct flag check
            m = re.search(r'haxagon\{[^}]+\}', text, re.IGNORECASE)
            if m:
                return m.group(0)
            # Extract the criminal's name (hidden under black rectangle)
            name_m = re.search(r'JMÉNO:\s*(.+?)(?:\n|DATUM)', text)
            if name_m:
                name = name_m.group(1).strip()
                # Format as flag: lowercase, spaces replaced with underscores
                slug = re.sub(r'\s+', '_', name.strip()).lower()
                return f"haxagon{{{slug}}}"
    except ImportError:
        pass
    finally:
        os.unlink(tmp)
    return None


@register("unix-newbie")
def unix_newbie(ctx: dict) -> str | None:
    """PENTAX RAW/TIFF with embedded JPEG — extract JPEG and OCR for flag."""
    import subprocess, zipfile, io, tempfile
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None
    if not ctx["files"]:
        return None
    resp = requests.get(ctx["files"][0], timeout=60)
    try:
        z = zipfile.ZipFile(io.BytesIO(resp.content))
    except Exception:
        return None
    for info in z.infolist():
        data = z.read(info.filename)
        with tempfile.NamedTemporaryFile(suffix=".pef", delete=False) as f:
            f.write(data)
            tmp_pef = f.name
        try:
            # Extract embedded JPEG from PENTAX RAW (TIFF-based PEF)
            jpg_result = subprocess.run(
                ["exiftool", "-b", "-JpgFromRaw", tmp_pef],
                capture_output=True, timeout=30
            )
            if jpg_result.stdout:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f2:
                    f2.write(jpg_result.stdout)
                    tmp_jpg = f2.name
                try:
                    img = Image.open(tmp_jpg)
                    text = pytesseract.image_to_string(img, lang="ces+eng")
                    flag_m = re.search(r'haxagon\{[^}]+\}', text)
                    if flag_m:
                        return flag_m.group(0)
                finally:
                    os.unlink(tmp_jpg)
        finally:
            os.unlink(tmp_pef)
    return None


@register("masterplan")
def masterplan(ctx: dict) -> str | None:
    """Maze grid — find path, decode using cipher key."""
    desc = ctx["description"]
    # Extract the cipher key: e.g. m4i16o7n2...
    key_m = re.search(r'([a-z]\d+(?:[a-z]\d+){5,})', desc)
    if not key_m:
        return None
    # Parse key: letter->number pairs (number = column index 1-16)
    pairs = re.findall(r'([a-z])(\d+)', key_m.group(0))
    # Map: column_number -> letter
    col_to_letter = {int(n): c for c, n in pairs}
    # Extract grid rows
    grid_rows = re.findall(r'^(?:[a-z0-9]  ){2,}[a-z0-9]', desc, re.MULTILINE)
    if not grid_rows:
        return None
    grid = [[cell.strip() for cell in row.split()] for row in grid_rows]
    if not grid:
        return None
    # Find safe path: traverse only '0' cells top-to-bottom
    # Try reading each column's character where '0' appears in each row
    # ... This puzzle needs more analysis to solve correctly
    return None
