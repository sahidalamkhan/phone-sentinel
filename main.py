import os
import re
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from curl_cffi import requests as cureq
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = "8873781750:AAGQM8fr7FMXnA-Az76ENswTXtjw17u2DyM"
TELEGRAM_CHAT_ID = "7726602615"

GADGET_EXCLUDES = [
    "case", "cover", "tempered", "lens", "protector", "skin", "sticker", 
    "vinyl", "wrap", "film", "lamination", "layer", "back", "pouch", 
    "camera glass", "compatible for", "dummy", "box only", "cleaner", 
    "decal", "bumper", "guard", "carbon fiber", "silicone", "toy", 
    "model only", "no motherboard", "faulty", "keypad", "feature phone", 
    "cable", "adapter", "battery", "charger", "earphone", "housing", "sim tray"
]

# Comprehensive 20-category tracking matrix
MASTER_TARGET_RULES = [
    # --- LAPTOP WRITING / DRAWING TABLETS ---
    {
        "name": "Pro Writing Pad (Wacom/XP-Pen/Huion)",
        "min_price": 500,
        "max_price": 1500,
        "keywords": ["graphic", "tablet"],
        "excludes": ["lcd", "rough", "toy", "slate", "nibs", "glove", "stand", "cable", "sleeve"],
        "flipkart_url": "https://www.flipkart.com/search?q=graphic+pen+tablet&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=graphic+drawing+pen+tablet&s=price-asc-rank"
    },

    # --- HIGH-SPEED SMARTPHONES & FLAGSHIP TABLETS ---
    {
        "name": "Google Pixel 10",
        "min_price": 10000,
        "max_price": 25000,
        "keywords": ["pixel 10"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=google+pixel+10&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=google+pixel+10&s=price-asc-rank"
    },
    {
        "name": "iPad M4",
        "min_price": 10000,
        "max_price": 27000,
        "keywords": ["ipad", "m4"],
        "excludes": GADGET_EXCLUDES + ["pencil", "sleeve", "keyboard"],
        "flipkart_url": "https://www.flipkart.com/search?q=ipad+m4&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=ipad+m4&s=price-asc-rank"
    },
    {
        "name": "Samsung Galaxy S26 Ultra",
        "min_price": 20000,
        "max_price": 50000,
        "keywords": ["s26 ultra"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=samsung+s26+ultra&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=samsung+s26+ultra&s=price-asc-rank"
    },
    {
        "name": "iPhone 18 Pro Max",
        "min_price": 40000,
        "max_price": 120000,
        "keywords": ["iphone 18 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+18+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+18+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 17 Pro Max",
        "min_price": 30000,
        "max_price": 100000,
        "keywords": ["iphone 17 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+17+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+17+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 16 Pro Max",
        "min_price": 20000,
        "max_price": 50000,
        "keywords": ["iphone 16 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+16+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+16+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 16 Pro",
        "min_price": 18000,
        "max_price": 40000,
        "keywords": ["iphone 16 pro"],
        "excludes": GADGET_EXCLUDES + ["max"],
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+16+pro&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+16+pro&s=price-asc-rank"
    },
    {
        "name": "iPhone 15 Pro Max",
        "min_price": 15000,
        "max_price": 40000,
        "keywords": ["iphone 15 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+15+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+15+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 14 Plus",
        "min_price": 10000,
        "max_price": 30000,
        "keywords": ["iphone 14 plus"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+14+plus&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+14+plus&s=price-asc-rank"
    },
    {
        "name": "Jio Bharat V4",
        "min_price": 50,
        "max_price": 920,
        "keywords": ["jio bharat v4"],
        "excludes": ["charger", "battery", "case", "cover", "earphone"],
        "flipkart_url": "https://www.flipkart.com/search?q=jio+bharat+v4&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=jio+bharat+v4&s=price-asc-rank"
    },

    # --- 2.5GHz+ GLITCH DROP RADARS (SAMSUNG, REALME, VIVO, OPPO, APPLE) ---
    {
        "name": "Samsung 5G Glitch Hunter",
        "min_price": 1,
        "max_price": 1000,
        "keywords": ["samsung", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=samsung+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=samsung+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Realme 5G Glitch Hunter",
        "min_price": 1,
        "max_price": 1000,
        "keywords": ["realme", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=realme+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=realme+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Vivo 5G Glitch Hunter",
        "min_price": 1,
        "max_price": 1000,
        "keywords": ["vivo", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=vivo+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=vivo+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Oppo 5G Glitch Hunter",
        "min_price": 1,
        "max_price": 1000,
        "keywords": ["oppo", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=oppo+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=oppo+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Apple iPhone Glitch Hunter",
        "min_price": 1,
        "max_price": 1000,
        "keywords": ["iphone"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone&s=price-asc-rank"
    },

    # --- OILS, GROCERY & DAILY ESSENTIALS ---
    {
        "name": "Mustard Oil 1L",
        "min_price": 40,
        "max_price": 100,
        "keywords": ["mustard oil", "1 l"],
        "excludes": ["15 l", "5 l", "500 ml", "200 ml", "bottle only"],
        "flipkart_url": "https://www.flipkart.com/search?q=mustard+oil+1l&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=mustard+oil+1l&s=price-asc-rank"
    },
    {
        "name": "Saloni Kachchhi Ghani 5L",
        "min_price": 200,
        "max_price": 500,
        "keywords": ["saloni", "5 l"],
        "excludes": ["1 l", "500 ml", "empty tin"],
        "flipkart_url": "https://www.flipkart.com/search?q=saloni+kachchi+ghani+5l&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=saloni+mustard+oil+5l&s=price-asc-rank"
    },
    {
        "name": "Parachute Coconut Oil 1L",
        "min_price": 60,
        "max_price": 200,
        "keywords": ["parachute", "1 l"],
        "excludes": ["body lotion", "500 ml", "200 ml", "100 ml"],
        "flipkart_url": "https://www.flipkart.com/search?q=parachute+coconut+oil+1l&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=parachute+coconut+oil+1l&s=price-asc-rank"
    },
    {
        "name": "Peter England Jeans 32",
        "min_price": 150,
        "max_price": 450,
        "keywords": ["peter england", "jeans"],
        "excludes": ["shirt", "t-shirt", "trouser", "tracksuit", "brief", "socks", "belt"],
        "flipkart_url": "https://www.flipkart.com/search?q=peter+england+jeans+32&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=peter+england+jeans+32&s=price-asc-rank"
    }
]

HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/"
}

# ==================== CLOUD KEEP-ALIVE SERVER ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Master Sentinel Cloud Engine is running 24/7.")

    # Fixes UptimeRobot 501 Not Implemented (UptimeRobot defaults to HEAD)
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Health check server listening on port {port}...", flush=True)
    server.serve_forever()

# ==================== TELEGRAM HANDLER & LISTENER ====================
def clean_price(price_str: str) -> int:
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else 0

def send_telegram_alert(title: str, price: int, platform: str, link: str):
    text = (
        f"🚨 <b>PRICE DROP / GLITCH DETECTED!</b>\n\n"
        f"<b>Item:</b> {title}\n"
        f"<b>Platform:</b> {platform}\n"
        f"<b>Price:</b> ₹{price:,}\n\n"
        f"⚡ <b>Tap below to buy immediately on your phone:</b>\n"
        f"👉 <a href='{link}'>OPEN PRODUCT / CHECKOUT</a>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=payload, timeout=8)
    except Exception as e:
        print(f"[!] Telegram alert failed: {e}", flush=True)

def telegram_message_listener():
    """Listens for user commands like /start and /status in Telegram"""
    offset = 0
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    while True:
        try:
            resp = requests.get(f"{base_url}/getUpdates?offset={offset}&timeout=20", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    text = msg.get("text", "")

                    if not chat_id:
                        continue

                    if text.startswith("/start"):
                        welcome_text = (
                            "👋 <b>Master Sentinel Bot is Active!</b>\n\n"
                            "✅ 24/7 Monitoring Enabled\n"
                            f"📡 Tracking <b>{len(MASTER_TARGET_RULES)}</b> deal categories\n"
                            "🔔 Price glitch alerts will arrive directly in this chat."
                        )
                        requests.post(
                            f"{base_url}/sendMessage",
                            data={"chat_id": chat_id, "text": welcome_text, "parse_mode": "HTML"},
                            timeout=8
                        )
                    elif text.startswith("/status"):
                        requests.post(
                            f"{base_url}/sendMessage",
                            data={"chat_id": chat_id, "text": "🟢 System Status: Active and running."},
                            timeout=8
                        )
        except Exception:
            pass
        time.sleep(1)

# ==================== PARSER AND SCRAPING ENGINES ====================
def validate_item(title: str, rule: dict) -> bool:
    t_low = title.lower()
    for ex in rule["excludes"]:
        if ex in t_low:
            return False
    for kw in rule["keywords"]:
        if kw not in t_low:
            return False
    return True

def scan_flipkart_feed(session, feed_url: str, rule: dict):
    items = []
    try:
        resp = session.get(feed_url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return items
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", {"class": re.compile(r"tUxRFH|cPHDOP|_1sdMkc")})
        for card in cards:
            title_el = card.find("div", {"class": re.compile(r"KzDlHZ|wjcEIp|_4rR01T")}) or card.find("a", {"title": True})
            price_el = card.find("div", {"class": re.compile(r"Nx9bqj|_30jeq3")})
            link_el = card.find("a", href=True)
            if title_el and price_el and link_el:
                title = title_el.get_text().strip() or title_el.get("title", "")
                if validate_item(title, rule):
                    items.append({
                        "title": title,
                        "price": clean_price(price_el.get_text()),
                        "link": "https://www.flipkart.com" + link_el["href"],
                        "platform": "Flipkart"
                    })
    except Exception:
        pass
    return items

def scan_amazon_feed(session, feed_url: str, rule: dict):
    items = []
    try:
        resp = session.get(feed_url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return items
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", {"data-component-type": "s-search-result"})
        for card in cards:
            title_el = card.find("h2")
            price_el = card.find("span", {"class": "a-price-whole"})
            link_el = card.find("a", {"class": "a-link-normal s-no-outline"}, href=True)
            if title_el and price_el and link_el:
                title = title_el.get_text().strip()
                if validate_item(title, rule):
                    raw_href = link_el["href"]
                    full_link = raw_href if raw_href.startswith("http") else "https://www.amazon.in" + raw_href
                    items.append({
                        "title": title,
                        "price": clean_price(price_el.get_text()),
                        "link": full_link,
                        "platform": "Amazon"
                    })
    except Exception:
        pass
    return items

# ==================== MAIN SCANNER LOOP ====================
def scanner_loop():
    print(f"Master Sentinel Loop active. Tracking {len(MASTER_TARGET_RULES)} categories 24/7...", flush=True)
    alerted_links = set()
    session = cureq.Session(impersonate="chrome120")

    while True:
        try:
            for rule in MASTER_TARGET_RULES:
                min_p = rule.get("min_price", 1)
                max_p = rule["max_price"]

                # 1. Sweep Flipkart
                fk_items = scan_flipkart_feed(session, rule["flipkart_url"], rule)
                for item in fk_items:
                    p = item["price"]
                    if min_p <= p <= max_p:
                        if item["link"] not in alerted_links:
                            alerted_links.add(item["link"])
                            print(f"[TARGET HIT] {item['title']} @ ₹{p:,} on Flipkart", flush=True)
                            send_telegram_alert(item["title"], p, "Flipkart", item["link"])
                time.sleep(2)

                # 2. Sweep Amazon
                amz_items = scan_amazon_feed(session, rule["amazon_url"], rule)
                for item in amz_items:
                    p = item["price"]
                    if min_p <= p <= max_p:
                        if item["link"] not in alerted_links:
                            alerted_links.add(item["link"])
                            print(f"[TARGET HIT] {item['title']} @ ₹{p:,} on Amazon", flush=True)
                            send_telegram_alert(item["title"], p, "Amazon", item["link"])
                time.sleep(2)

            print("Sweep cycle complete across all categories. Resting 60s...", flush=True)
        except Exception as e:
            print(f"[!] Scanner loop exception: {e}", flush=True)

        time.sleep(60)

# ==================== EXECUTION ENTRY POINT ====================
if __name__ == "__main__":
    # 1. Run web server in background to keep Render alive
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()

    # 2. Run Telegram listener to handle /start and incoming messages
    t_bot = threading.Thread(target=telegram_message_listener, daemon=True)
    t_bot.start()

    # 3. Send confirmation ping to Telegram
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": "🟢 <b>Master Sentinel Bot is online and tracking deals!</b>",
                "parse_mode": "HTML"
            },
            timeout=8
        )
    except Exception as e:
        print(f"[!] Startup ping failed: {e}", flush=True)

    # 4. Start main scanner loop
    scanner_loop()
