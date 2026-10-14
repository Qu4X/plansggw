#!/usr/bin/env python3
"""
generate_screenshots.py — Generuje zrzuty ekranu dla manifestu PWA (desktop i mobile)
wykorzystując lokalnie zainstalowaną przeglądarkę Chrome/Edge przez Playwright.
"""
import os
import sys
from playwright.sync_api import sync_playwright

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(REPO_ROOT, "web")
DIST_DIR = os.path.join(REPO_ROOT, "dist")

DESKTOP_PATH = os.path.join(WEB_DIR, "screenshot-desktop.png")
MOBILE_PATH = os.path.join(WEB_DIR, "screenshot-mobile.png")

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
]


def find_browser_executable() -> str:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    raise RuntimeError("Nie znaleziono pliku wykonywalnego Chrome ani Edge!")


def generate_screenshots():
    exe_path = find_browser_executable()
    print(f"Using browser: {exe_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe_path, headless=True)

        # 1. Desktop Screenshot (1280x720)
        print("Generating Desktop screenshot (1280x720)...")
        desktop_context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1
        )
        desktop_page = desktop_context.new_page()

        # Pre-set localStorage so plan is loaded immediately
        desktop_page.add_init_script("""
            localStorage.setItem('sggw_selected_plan', 'wmw_sem_7');
            localStorage.setItem('sggw_selected_group', 'gr. 1');
            localStorage.setItem('sggw_theme', 'dark');
            localStorage.setItem('sggw_days_view', 'workdays');
            localStorage.setItem('last_seen_changelog_version', '1.0.0');
        """)

        desktop_page.goto("http://localhost:8000/", wait_until="networkidle")
        desktop_page.wait_for_selector(".lesson-card", timeout=10000)
        desktop_page.wait_for_timeout(1000)  # Stabilize rendering

        desktop_page.screenshot(path=DESKTOP_PATH)
        print(f"[OK] Saved {DESKTOP_PATH}")
        desktop_context.close()

        # 2. Mobile Screenshot (720x1280)
        print("Generating Mobile screenshot (720x1280)...")
        mobile_context = browser.new_context(
            viewport={"width": 720, "height": 1280},
            device_scale_factor=1,
            is_mobile=True,
            has_touch=True
        )
        mobile_page = mobile_context.new_page()

        mobile_page.add_init_script("""
            localStorage.setItem('sggw_selected_plan', 'wmw_sem_7');
            localStorage.setItem('sggw_selected_group', 'gr. 1');
            localStorage.setItem('sggw_theme', 'dark');
            localStorage.setItem('sggw_days_view', 'workdays');
            localStorage.setItem('last_seen_changelog_version', '1.0.0');
        """)

        mobile_page.goto("http://localhost:8000/", wait_until="networkidle")
        mobile_page.wait_for_selector(".lesson-card", timeout=10000)

        # Na telefonie wybieramy widok pojedynczego dnia (np. Poniedziałek)
        pon_tab = mobile_page.locator('.day-tab[data-day="PON"]')
        if pon_tab.count() > 0:
            pon_tab.click()

        mobile_page.wait_for_timeout(1000)

        mobile_page.screenshot(path=MOBILE_PATH)
        print(f"[OK] Saved {MOBILE_PATH}")
        mobile_context.close()

        browser.close()

    # Kopiowanie do dist/ jeśli istnieje
    if os.path.exists(DIST_DIR):
        import shutil
        shutil.copy2(DESKTOP_PATH, os.path.join(DIST_DIR, "screenshot-desktop.png"))
        shutil.copy2(MOBILE_PATH, os.path.join(DIST_DIR, "screenshot-mobile.png"))
        print("[OK] Copied screenshots to dist/")


if __name__ == "__main__":
    generate_screenshots()
