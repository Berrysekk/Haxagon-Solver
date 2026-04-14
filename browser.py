# browser.py
import asyncio
from playwright.async_api import async_playwright, Page, Browser

BASE_URL = "https://haxagon.xyz"

class HaxagonBrowser:
    def __init__(self):
        self._pw = None
        self._browser: Browser = None
        self.page: Page = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        self.page = await self._browser.new_page()
        return self

    async def __aexit__(self, *_):
        try:
            await self._browser.close()
        finally:
            await self._pw.stop()

    async def login(self, email: str, password: str) -> bool:
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.fill('input[type="email"], input[name="email"]', email)
        await self.page.fill('input[type="password"], input[name="password"]', password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        return await self._check_login_success()

    async def _check_login_success(self) -> bool:
        el = await self.page.query_selector('[data-testid="user-menu"], .user-avatar, .logout-btn')
        return el is not None

    async def navigate_to_skirmish(self):
        await self.page.goto(f"{BASE_URL}/skirmish")
        await self.page.wait_for_load_state("networkidle")

    async def list_challenges(self) -> list[dict]:
        """Return [{slug, name, xp, solved}] for all visible challenges."""
        await self.navigate_to_skirmish()
        cards = await self.page.query_selector_all('.challenge-card, [data-challenge-id]')
        result = []
        for card in cards:
            slug = await card.get_attribute('data-challenge-slug') or await card.get_attribute('id') or ''
            name_el = await card.query_selector('.challenge-name, h3, h2')
            name = (await name_el.inner_text()).strip() if name_el else slug
            xp_el = await card.query_selector('.xp, .points')
            if xp_el:
                try:
                    xp = int((await xp_el.inner_text()).strip().replace('xp','').replace(' ',''))
                except ValueError:
                    xp = 0
            else:
                xp = 0
            solved_el = await card.query_selector('.solved, .completed, [data-solved="true"]')
            result.append({'slug': slug, 'name': name, 'xp': xp, 'solved': solved_el is not None})
        return result

    async def open_challenge(self, slug: str) -> dict:
        """Navigate to challenge page, return {description, files, page}."""
        await self.page.goto(f"{BASE_URL}/skirmish/{slug}")
        await self.page.wait_for_load_state("networkidle")
        desc_el = await self.page.query_selector('.challenge-description, .description, article')
        description = (await desc_el.inner_text()).strip() if desc_el else ''
        file_links = await self.page.eval_on_selector_all(
            'a[href*="/download"], a[href*="/files"], a[download]',
            'els => els.map(e => e.href)'
        )
        return {'description': description, 'files': file_links, 'page': self.page}

    async def submit_flag(self, slug: str, flag: str) -> bool:
        """Submit flag, return True if accepted."""
        flag_input = await self.page.query_selector('input[name="flag"], input[placeholder*="flag"], input[placeholder*="CTF"]')
        if not flag_input:
            return False
        await flag_input.fill(flag)
        submit_btn = await self.page.query_selector('button[type="submit"], button:has-text("Submit")')
        if submit_btn:
            await submit_btn.click()
        await self.page.wait_for_load_state("networkidle")
        success_el = await self.page.query_selector('.correct, .success, [data-correct="true"]')
        return success_el is not None
