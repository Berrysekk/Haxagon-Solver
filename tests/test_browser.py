# tests/test_browser.py
import pytest
from browser import HaxagonBrowser

@pytest.mark.asyncio
async def test_check_login_success_returns_true_when_element_found():
    """_check_login_success returns True when URL is not the sign-in page."""
    class FakePage:
        url = "https://haxagon.xyz/"
    browser = HaxagonBrowser.__new__(HaxagonBrowser)
    browser.page = FakePage()
    result = await browser._check_login_success()
    assert result is True

@pytest.mark.asyncio
async def test_check_login_success_returns_false_when_no_element():
    """_check_login_success returns False when still on sign-in page."""
    class FakePage:
        url = "https://haxagon.xyz/sign/in"
    browser = HaxagonBrowser.__new__(HaxagonBrowser)
    browser.page = FakePage()
    result = await browser._check_login_success()
    assert result is False
