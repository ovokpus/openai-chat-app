"""Headless Playwright screenshots of the running stack (docker compose up) -> docs/screenshots/.
No real OpenAI key is used. The 'rejected key' shot uses the obviously fake key below, so the
screen shows the app's real error and no model output."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'screenshots'
UI = 'http://localhost:3000'
FAKE_KEY = 'sk-not-a-real-key'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1366, 'height': 900}, device_scale_factor=2)
        pg.goto(UI, wait_until='networkidle'); pg.wait_for_timeout(1500)
        pg.screenshot(path=OUT / 'home-no-key.png')
        key = pg.locator('input[placeholder="sk-..."]')
        if not key.is_visible():
            pg.locator('header button').last.click(); pg.wait_for_timeout(500)
        pg.screenshot(path=OUT / 'api-key-panel.png')
        key.fill(FAKE_KEY)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(800)  # key entered: the upload panel appears
        pg.screenshot(path=OUT / 'upload-panel.png')
        pg.fill('input[placeholder="Type your message..."]', 'Summarise Basel III in two sentences.')
        pg.keyboard.press('Enter'); pg.wait_for_timeout(6000)
        pg.screenshot(path=OUT / 'chat-rejected-key.png')
        pg.goto('http://localhost:8000/docs'); pg.wait_for_selector('.opblock')
        pg.screenshot(path=OUT / 'api-docs.png')
        b.close()


if __name__ == '__main__':
    main()
