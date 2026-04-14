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
        await self.page.goto(f"{BASE_URL}/sign/in")
        await self.page.wait_for_load_state("networkidle")
        await self.page.click('button:has-text("E-mail")')
        await self.page.wait_for_timeout(500)
        await self.page.locator('input[placeholder="Email"]').fill(email)
        await self.page.locator('input[placeholder="Password"]').click()
        await self.page.locator('input[placeholder="Password"]').type(password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_timeout(5000)
        return await self._check_login_success()

    async def _check_login_success(self) -> bool:
        return "/sign/in" not in self.page.url

    async def navigate_to_skirmish(self):
        await self.page.goto(f"{BASE_URL}/competition/skirmish")
        await self.page.wait_for_load_state("networkidle")

    async def list_challenges(self) -> list[dict]:
        """Return [{slug, name, xp, solved}] for all visible challenges."""
        await self.navigate_to_skirmish()
        await self.page.wait_for_timeout(1000)
        links = await self.page.query_selector_all('a[href*="/competition/skirmish/challenge/"]')
        seen = set()
        result = []
        for link in links:
            href = await link.get_attribute('href')
            if not href or href in seen:
                continue
            seen.add(href)
            slug = href.split('/')[-1]
            name_el = await link.query_selector('p[class*="text-grey"]')
            name = (await name_el.inner_text()).strip() if name_el else slug
            xp_text = await link.inner_text()
            try:
                import re
                xp = int(re.search(r'\+(\d+)xp', xp_text).group(1))
            except (AttributeError, ValueError):
                xp = 0
            result.append({'slug': slug, 'name': name, 'xp': xp, 'solved': False})
        return result

    async def open_challenge(self, slug: str) -> dict:
        """Navigate to challenge page, return {description, files, page}."""
        await self.page.goto(f"{BASE_URL}/competition/skirmish/challenge/{slug}")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(500)
        desc_el = await self.page.query_selector('h1, h2, .challenge-description, article p')
        description = (await desc_el.inner_text()).strip() if desc_el else ''
        file_links = await self.page.eval_on_selector_all(
            'a[href*="/download"], a[href*="/files"], a[download]',
            'els => els.map(e => e.href)'
        )
        return {'description': description, 'files': file_links, 'page': self.page}

    async def submit_flag(self, slug: str, flag: str) -> bool:
        """Submit flag, return True if accepted."""
        flag_input = await self.page.query_selector('input[placeholder="Your answer"]')
        if not flag_input:
            return False
        await flag_input.fill(flag)
        submit_btn = await self.page.query_selector('button:has-text("Check")')
        if submit_btn:
            await submit_btn.click()
        await self.page.wait_for_timeout(2000)
        success_el = await self.page.query_selector('[class*="completed"], [class*="correct"], [class*="success"]')
        return success_el is not None
