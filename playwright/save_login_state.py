import asyncio
from playwright.async_api import async_playwright

SAVE_PATH = "user_data/login_state.json"
TARGET_URL = "https://aisheets-sheets.hf.space/"

async def save_login_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(TARGET_URL)

        print("\n[🧠] Bitte logge dich manuell ein.")
        input("🔐 Wenn du fertig bist, drücke Enter, um Login zu speichern...")

        await context.storage_state(path=SAVE_PATH)
        print(f"[✅] Login-State gespeichert unter {SAVE_PATH}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_login_state())
