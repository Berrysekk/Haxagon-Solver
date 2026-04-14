import io
from PIL import Image, ImageEnhance

def brighten(filepath: str, factor: float = 3.0) -> bytes:
    """Return brightened image as PNG bytes."""
    img = Image.open(filepath).convert("RGB")
    enhanced = ImageEnhance.Brightness(img).enhance(factor)
    buf = io.BytesIO()
    enhanced.save(buf, format="PNG")
    return buf.getvalue()

def extract_text_from_image(filepath: str) -> str:
    """OCR via pytesseract if available, else empty string."""
    try:
        import pytesseract
        return pytesseract.image_to_string(Image.open(filepath))
    except ImportError:
        return ""

def scan_qr(filepath: str) -> str | None:
    """Decode first QR code found in image."""
    from pyzbar.pyzbar import decode as pyzbar_decode
    img = Image.open(filepath)
    codes = pyzbar_decode(img)
    return codes[0].data.decode() if codes else None
