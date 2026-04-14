# tests/test_browser.py
import pytest
from browser import HaxagonBrowser

@pytest.mark.asyncio
async def test_check_login_success_returns_true_when_element_found():
    """_check_login_success returns True when the user-menu element is present."""
    class FakePage:
        async def goto(self, url): pass
        async def fill(self, sel, val): pass
        async def click(self, sel): pass
        async def wait_for_load_state(self, state): pass
        async def query_selector(self, sel): return object()  # non-None = found
    browser = HaxagonBrowser.__new__(HaxagonBrowser)
    browser.page = FakePage()
    result = await browser._check_login_success()
    assert result is True

@pytest.mark.asyncio
async def test_check_login_success_returns_false_when_no_element():
    class FakePage:
        async def query_selector(self, sel): return None
    browser = HaxagonBrowser.__new__(HaxagonBrowser)
    browser.page = FakePage()
    result = await browser._check_login_success()
    assert result is False
