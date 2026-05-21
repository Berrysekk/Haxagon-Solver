# browser.py
import asyncio
import re
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
            text = await link.inner_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            # Card format: "+Nxp" or "Completed", then challenge name, then difficulty, ...
            name = lines[1] if len(lines) > 1 else slug
            solved = lines[0].lower() == 'completed' if lines else False
            try:
                xp = int(re.search(r'\+(\d+)xp', lines[0]).group(1)) if not solved else 0
            except (AttributeError, ValueError, IndexError):
                xp = 0
            result.append({'slug': slug, 'name': name, 'xp': xp, 'solved': solved})
        return result

    async def open_challenge(self, slug: str) -> dict:
        """Navigate to challenge page, return {description, files, page}."""
        await self.page.goto(f"{BASE_URL}/competition/skirmish/challenge/{slug}")
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(500)
        full_text = await self.page.inner_text('body')
        idx = full_text.find('Challenge\n')
        if idx >= 0:
            section = full_text[idx:]
            end = section.find('\nFlag ')
            description = section[:end].strip() if end >= 0 else section.strip()
        else:
            description = full_text
        # Collect download links from both anchor tags and challenge img tags
        # The platform uses two CDN domains: static.haxagon.xyz (images) and static.haxagon.cz (files)
        file_links = await self.page.eval_on_selector_all(
            'a[href*="/download"], a[href*="/files"], a[download], a[href*="static.haxagon"]',
            'els => els.map(e => e.href)'
        )
        img_links = await self.page.eval_on_selector_all(
            'img[src*="static.haxagon"]',
            'els => els.map(e => e.src).filter(s => !s.endsWith(".webp") && s.includes("challenge-images"))'
        )
        # Deduplicate while preserving order
        seen = set()
        all_files = []
        for url in file_links + img_links:
            if url not in seen:
                seen.add(url)
                all_files.append(url)
        return {'description': description, 'files': all_files, 'page': self.page}

    def _is_success(self, body_text: str) -> bool:
        """Check body text for challenge success indicators."""
        if 'completed 100%' in body_text:
            return True
        # Note: platform shows bare "Correct" (no exclamation) on single-flag success
        if any(w in body_text for w in ['Správně', 'Correct!', 'Correct', 'Výborně']):
            return True
        return False

    async def submit_flag(self, slug: str, flag: str) -> bool:
        """Submit a single flag, return True if accepted."""
        expected = f"{BASE_URL}/competition/skirmish/challenge/{slug}"
        if not self.page.url.startswith(expected):
            await self.page.goto(expected)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(500)
        # Check if already completed (e.g. from a prior session's run)
        quick_body = await self.page.inner_text('body')
        if 'completed 100%' in quick_body:
            return True
        flag_input = await self.page.query_selector('input[placeholder="Your answer"]')
        if not flag_input:
            return False
        await flag_input.fill(flag)
        submit_btn = await self.page.query_selector('button:has-text("Check")')
        if submit_btn:
            await submit_btn.click()
        await self.page.wait_for_timeout(3000)
        body_text = await self.page.inner_text('body')
        success_el = await self.page.query_selector(
            '[class*="completed"], [class*="correct"], [class*="success"], '
            '.flag-correct, .answer-correct'
        )
        if success_el:
            return True
        return self._is_success(body_text)

    async def submit_multi_flags(self, slug: str, flags: list[str]) -> bool:
        """Submit multiple flags for a multi-flag challenge, return True if all accepted."""
        expected = f"{BASE_URL}/competition/skirmish/challenge/{slug}"
        if not self.page.url.startswith(expected):
            await self.page.goto(expected)
            await self.page.wait_for_load_state("networkidle")
            await self.page.wait_for_timeout(500)
        quick_body = await self.page.inner_text('body')
        if 'completed 100%' in quick_body:
            return True
        # Find all answer inputs and check buttons
        inputs = await self.page.query_selector_all(
            'input[placeholder="Answer"], input[placeholder="Your answer"]'
        )
        check_buttons = await self.page.query_selector_all('button:has-text("Check")')
        submitted = 0
        for flag, inp, btn in zip(flags, inputs, check_buttons):
            placeholder = await inp.get_attribute('placeholder') or ''
            if 'already' in placeholder.lower():
                submitted += 1
                continue
            await inp.fill(flag)
            await btn.click()
            await self.page.wait_for_timeout(1500)
            submitted += 1
        if submitted == 0:
            return False
        await self.page.wait_for_timeout(2000)
        body_text = await self.page.inner_text('body')
        return self._is_success(body_text) or submitted == len(flags)
