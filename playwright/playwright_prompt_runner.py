import asyncio
import datetime
from pathlib import Path
from playwright.async_api import async_playwright

PROMPT_FILE = "prompts.txt"
SCREENSHOT_DIR = Path("results/screenshots")
USER_DATA_DIR = "user_data"

async def export_parquet_for_prompt(page, prompt_text, i):
    print(f"\n[🧠] Prompt {i+1}: {prompt_text}")

    # Prompt-Feld füllen
    await page.wait_for_selector("textarea#prompt", timeout=30_000)
    await page.locator("textarea#prompt").fill(prompt_text)

    # Absenden
    print("[📤] Prompt absenden...")
    await page.keyboard.press("Enter")  # besser als auf 'Submit'-Button warten

    # Warte auf mögliche Antwort
    print("[⏳] Warte auf Antwort...")
    await asyncio.sleep(35)  # Optional dynamisch anpassbar

    # Export starten
    print("[📦] Suche Menü-Button für Export...")
    try:
        await page.wait_for_selector("button[popovertarget]", timeout=10_000)
        await page.locator("button[popovertarget]").first.click()
    except Exception as e:
        print(f"[❌] Menü-Button nicht gefunden: {e}")
        return

    # Parquet finden und klicken
    print("[⬇️ ] Suche 'Download Parquet'...")
    try:
        await page.wait_for_selector("button:has(div:has-text('Download Parquet'))", timeout=10_000)
        parquet_button = page.locator("button:has(div:has-text('Download Parquet'))")

        async with page.expect_download() as download_info:
            await parquet_button.click()
        download = await download_info.value

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        save_path = SCREENSHOT_DIR / f"run_{i}_{timestamp}.parquet"
        await download.save_as(save_path)
        print(f"[✅] Parquet gespeichert: {save_path}")

    except Exception as e:
        print(f"[❌] Fehler beim Parquet-Download: {e}")

    # Zurück zur Startseite für den nächsten Prompt
    print("[🔙] Zurück zur Prompt-Seite...")
    await page.go_back()
    await page.wait_for_selector("textarea#prompt", timeout=30_000)
    print("[🔄] Promptfeld erneut verfügbar.")

    await asyncio.sleep(2)

    
async def run():
    prompts = [line.strip() for line in Path(PROMPT_FILE).read_text(encoding="utf-8").splitlines() if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={"width": 1400, "height": 1000},
            accept_downloads=True
        )
        page = await browser.new_page()

        # Seite öffnen & reload für Login
        await page.goto("https://aisheets-sheets.hf.space/")
        await page.reload()
        print("[🔁] Seite neu geladen – Login sichtbar machen...")

        # Warte auf Prompt-Feld
        print("[🧠] Warte auf Prompt-Feld...")
        await page.wait_for_selector("textarea#prompt", timeout=30_000)
        print("[✅] Promptfeld bereit.")

        # Durchlauf
        for i, prompt in enumerate(prompts):
            await export_parquet_for_prompt(page, prompt.strip(), i)

        print("\n🏁 Alle Prompts durchlaufen.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
