#  Shaalaa Link Scraper


https://github.com/user-attachments/assets/a8d3985d-7f00-4991-9b96-39ac8ab0851d

A Python-based web scraper that searches [DuckDuckGo](https://duckduckgo.com) and extracts relevant links from [shaalaa.com](https://www.shaalaa.com) — a popular Maharashtra State Board study resource — for any given topic and class.

---

##  What It Does

1. Takes a **topic query**, **standard (class)**, and **board** as input
2. Opens DuckDuckGo in a real Chrome window using Selenium
3. Searches for `<query> site:shaalaa.com` scoped to the given class and board
4. Extracts and returns the **top 3 matching shaalaa.com links**
5. Saves them to `data/links.txt`


---



##  Tech Stack

| Tool | Purpose |
|---|---|
| `selenium` | Browser automation |
| `webdriver-manager` | Auto-installs the correct ChromeDriver |
| `BeautifulSoup` | HTML parsing (requests-based version) |
| `FastAPI` | REST API layer |
| `uvicorn` | ASGI server |

---


##  Setup

**1. Clone the repo**
```bash
git clone https://github.com/your-username/shaalaa-scraper.git
cd shaalaa-scraper
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### Option A — Run directly (Selenium, visible browser)

```bash
python scripts/selenium_scraper.py
```

You'll be prompted to enter a search query:

```
Enter your search query: digestive system
```

Chrome will open, search DuckDuckGo, and print the found links:

```
🔗 Found 3 link(s):
  • https://www.shaalaa.com/...
  • https://www.shaalaa.com/...
  • https://www.shaalaa.com/...
```

---

### Option B — Run as a FastAPI server

```bash
python scripts/finalscraping.py
```

Then hit the endpoint in your browser or via curl:

```
GET http://localhost:8000/getlinks?query=digestive+system&std=7&board=Maharashtra+state+board
```

**Response:**
```json
{
  "links": [
    "https://www.shaalaa.com/...",
    "https://www.shaalaa.com/..."
  ],
  "count": 2
}
```

---

##  How Bot Detection Is Handled

DuckDuckGo can flag automated requests. This scraper reduces that risk by:

- Using a **random User-Agent** from a pool of real Chrome UAs each run
- **Typing characters one-by-one** with randomised delays (mimics human typing)
- Adding **random pauses** at natural moments (page load, before submit, after results)
- Patching `navigator.webdriver` to `undefined` via Chrome DevTools Protocol
- Disabling Selenium's automation flags (`--disable-blink-features=AutomationControlled`)
- Running in a **visible (non-headless) browser** — headless is easier to fingerprint

> If you get repeated failures, your IP may be temporarily soft-banned by DDG. Wait a few minutes before retrying.

---

##  Debugging

If a search fails, the scraper automatically saves debug files:

| File | When it's created |
|---|---|
| `debug_no_searchbox.png` | Search box wasn't found on the page |
| `debug_no_results.png` + `.html` | Results didn't load (possible CAPTCHA) |
| `debug_no_shaalaa.png` | Results loaded but no shaalaa.com links found |

---
<img width="780" height="493" alt="debug_no_results" src="https://github.com/user-attachments/assets/37737e1c-c92c-4be2-b635-11e8b6067e34" />

## 📋 Requirements

```
selenium
webdriver-manager
beautifulsoup4
requests
fastapi
uvicorn
```

---

## 📌 Notes

- Default class: **Std 7**
- Default board: **Maharashtra State Board**
- Both are configurable via query parameters (API) or function arguments (script)
- Max links returned: **3** (configurable via `max_links` parameter)

---

## 📄 License

MIT
