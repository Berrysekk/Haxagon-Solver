import time
import requests

def crack_hash(hash_value: str) -> str | None:
    """
    Submit hash to CrackStation API, return plaintext or None.
    Respects rate limiting with 2s sleep.
    """
    time.sleep(2)
    try:
        resp = requests.post(
            "https://crackstation.net/crack.js",
            data={"hash": hash_value, "key": ""},
            headers={"Referer": "https://crackstation.net/"},
            timeout=30
        )
        data = resp.json()
        if isinstance(data, list) and data and data[0].get("result"):
            return data[0]["result"]
    except Exception:
        pass
    return None
