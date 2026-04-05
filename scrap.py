import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs
import time

# ── Realistic user agents (real Chrome versions, real OSes) ─────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def human_delay(min_s: float = 0.8, max_s: float = 2.0) -> None:
    """Sleep for a random duration to mimic human reaction time."""
    t = random.uniform(min_s, max_s)
    print(f"  ⏱️  Human pause: {t:.2f}s")
    time.sleep(t)


def human_type(element, text: str) -> None:
    """Type one character at a time with randomised delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.18))


def build_driver() -> webdriver.Chrome:
    options = Options()

    # ── Visible window ───────────────────────────────────────────────
    # options.add_argument("--headless")   ← keep off; headless = easier to detect
    options.add_argument("--start-maximized")

    # ── Anti-detection ───────────────────────────────────────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ── Random user-agent ────────────────────────────────────────────
    ua = random.choice(USER_AGENTS)
    options.add_argument(f"--user-agent={ua}")
    print(f"🕵️  Using User-Agent: {ua[:60]}…")

    # ── Misc stability ───────────────────────────────────────────────
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(20)

    # Patch navigator.webdriver to undefined (hides Selenium flag)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver


def normalise_href(href: str) -> str:
    """Unwrap DDG redirect and normalise the scheme."""
    if "uddg=" in href:
        parsed = urlparse(href)
        href   = parse_qs(parsed.query).get("uddg", [href])[0]
    if href.startswith("//"):
        return "https:" + href
    if not href.startswith("http"):
        return "https://" + href
    return href


def get_links_selenium(
    query:     str,
    std:       int = 7,
    board:     str = "Maharashtra state board",
    max_links: int = 3,
    timeout:   int = 10,
) -> list[str]:
    search_query = f"{query} std {std} {board} site:shaalaa.com"
    driver = build_driver()
    wait   = WebDriverWait(driver, timeout)

    try:
        # ── 1. Load DDG ──────────────────────────────────────────────
        print("\n🌐 Opening DuckDuckGo…")
        try:
            driver.get("https://duckduckgo.com/html/")
        except WebDriverException as e:
            raise RuntimeError(f"Failed to load DuckDuckGo: {e}") from e

        human_delay(1.0, 2.5)   # pause like a human would after page load

        # ── 2. Find search box ───────────────────────────────────────
        print("🔍 Locating search box…")
        try:
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        except TimeoutException:
            driver.save_screenshot("debug_no_searchbox.png")
            raise RuntimeError(
                f"Search box not found within {timeout}s. "
                "Screenshot → debug_no_searchbox.png"
            )

        # ── 3. Type like a human ─────────────────────────────────────
        print(f"⌨️  Typing query: {search_query!r}")
        search_box.clear()
        human_type(search_box, search_query)

        human_delay(0.3, 0.9)   # brief pause before hitting Enter
        search_box.send_keys(Keys.RETURN)

        # ── 4. Wait for results ──────────────────────────────────────
        print("⏳ Waiting for results…")
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "result__a")))
        except TimeoutException:
            driver.save_screenshot("debug_no_results.png")
            with open("debug_no_results.html", "w") as f:
                f.write(driver.page_source)
            raise RuntimeError(
                f"No results within {timeout}s — possible CAPTCHA or rate-limit. "
                "Screenshot → debug_no_results.png  |  HTML → debug_no_results.html"
            )

        human_delay(0.5, 1.2)   # pause before scraping, like a human reading

        # ── 5. Parse & filter ────────────────────────────────────────
        result_divs = driver.find_elements(By.CLASS_NAME, "result")
        print(f"\n📄 {len(result_divs)} result(s) found. Filtering shaalaa.com…\n")

        if not result_divs:
            raise RuntimeError("No result divs found — DDG layout may have changed.")

        links: list[str] = []

        for idx, result in enumerate(result_divs, start=1):
            if len(links) >= max_links:
                break
            try:
                a_tag = result.find_element(By.CLASS_NAME, "result__a")
                href  = a_tag.get_attribute("href")

                if not href:
                    print(f"  [{idx}] ⚠️  Empty href, skipping.")
                    continue

                href = normalise_href(href)

                if "shaalaa.com" not in href:
                    print(f"  [{idx}] ⏭️  Skipped → {href[:70]}")
                    continue

                print(f"  [{idx}] ✅ {href}")
                links.append(href)

            except NoSuchElementException:
                print(f"  [{idx}] ⚠️  No anchor in this block, skipping.")

        if not links:
            driver.save_screenshot("debug_no_shaalaa.png")
            print("\n⚠️  No shaalaa.com links found. Screenshot → debug_no_shaalaa.png")

        return links

    finally:
        time.sleep(1)  # brief pause before closing, so you can see the final state
        driver.quit()
        print("🛑 Browser closed.")


if __name__ == "__main__":
    query = input("Enter your search query: ").strip()
    if not query:
        print("❌ Query cannot be empty.")
        exit(1)

    try:
        links = get_links_selenium(query)
    except RuntimeError as e:
        print(f"\n❌ FAILED: {e}")
        exit(1)

    if links:
        print(f"\n🔗 Found {len(links)} link(s):")
        for link in links:
            print(f"  • {link}")
    else:
        print("\n⚠️  No links returned.")