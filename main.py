
import os
import re
import sys
import time
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from curl_cffi import requests as cureq
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = "8873781750:AAGQM8fr7FMXnA-Az76ENswTXtjw17u2DyM"
TELEGRAM_CHAT_ID = "7726602615"

# Robust negative keywords to filter cases, covers, screen guards, and accessories
GADGET_EXCLUDES = [
    "case", "cover", "tempered", "lens", "protector", "skin", "sticker", 
    "vinyl", "wrap", "film", "lamination", "layer", "back", "pouch", 
    "camera glass", "compatible for", "dummy", "box only", "cleaner", 
    "decal", "bumper", "guard", "carbon fiber", "silicone", "toy", 
    "model only", "no motherboard", "faulty", "keypad", "feature phone", 
    "cable", "adapter", "battery", "charger", "earphone", "housing", "sim tray",
    "clear", "yellowing", "shockproof", "anti-scratch", "transparent", 
    "matte", "hybrid", "armor", "magsafe case", "stand", "holder"
]

MASTER_TARGET_RULES = [
    {
        "name": "Google Pixel 10",
        "min_price": 1000,
        "glitch_max": 25000,
        "keywords": ["pixel 10"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=google+pixel+10&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=google+pixel+10&s=price-asc-rank"
    },
    {
        "name": "Apple iPad M4",
        "min_price": 1000,
        "glitch_max": 27000,
        "keywords": ["ipad", "m4"],
        "excludes": GADGET_EXCLUDES + ["pencil", "sleeve", "keyboard"],
        "flipkart_url": "https://www.flipkart.com/search?q=ipad+m4&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=ipad+m4&s=price-asc-rank"
    },
    {
        "name": "Samsung S26 Ultra",
        "min_price": 1000,
        "glitch_max": 50000,
        "keywords": ["s26 ultra"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=samsung+s26+ultra&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=samsung+s26+ultra&s=price-asc-rank"
    },
    {
        "name": "iPhone 18 Pro Max",
        "min_price": 1000,
        "glitch_max": 120000,
        "keywords": ["iphone 18 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+18+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+18+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 17 Pro Max",
        "min_price": 1000,
        "glitch_max": 100000,
        "keywords": ["iphone 17 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+17+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+17+pro+max&s=price-asc-rank"
    },
    {
        "name": "iPhone 16 Pro Max",
        "min_price": 1000,
        "glitch_max": 50000,
        "keywords": ["iphone 16 pro max"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone+16+pro+max&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone+16+pro+max&s=price-asc-rank"
    },
    {
        "name": "Samsung 5G Hunter",
        "min_price": 1,
        "glitch_max": 1000,
        "keywords": ["samsung", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=samsung+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=samsung+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Realme 5G Hunter",
        "min_price": 1,
        "glitch_max": 1000,
        "keywords": ["realme", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=realme+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=realme+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Vivo 5G Hunter",
        "min_price": 1,
        "glitch_max": 1000,
        "keywords": ["vivo", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=vivo+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=vivo+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Oppo 5G Hunter",
        "min_price": 1,
        "glitch_max": 1000,
        "keywords": ["oppo", "5g"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=oppo+5g+smartphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=oppo+5g+smartphone&s=price-asc-rank"
    },
    {
        "name": "Apple Glitch Hunter",
        "min_price": 1,
        "glitch_max": 1000,
        "keywords": ["iphone"],
        "excludes": GADGET_EXCLUDES,
        "flipkart_url": "https://www.flipkart.com/search?q=iphone&sort=price_asc",
        "amazon_url": "https://www.amazon.in/s?k=iphone&s=price-asc-rank"
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

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Health check server listening on port {port}...", flush=True)
    server.serve_forever()

# ==================== TELEGRAM DISPATCH ====================
def clean_price(price_str: str) -> int:
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else 0

def send_telegram_raw(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram request failed: {e}", flush=True)

def send_instant_glitch_alert(title: str, price: int, platform: str, link: str):
    msg = (
        f"🚨 <b>REAL GLITCH DROP CONFIRMED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Item:</b> {title}\n"
        f"🏷 <b>Platform:</b> {platform}\n"
        f"💰 <b>Price:</b> ₹{price:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <a href='{link}'><b>[TAP HERE TO BUY IMMEDIATELY]</b></a>"
    )
    send_telegram_raw(msg)

def send_gui_dashboard(market_summary: list):
    now_str = datetime.datetime.now().strftime("%I:%M %p")
    header = (
        f"📊 <b>LIVE SENTINEL MARKET DASHBOARD</b>\n"
        f"🕒 <i>Synced: {now_str} IST | Status: Active</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    body = ""
    for item in market_summary:
        name = item['name']
        price = item['price']
        platform = item['platform']
        link = item['link']
        
        if price > 0:
            price_display = f"₹{price:,}"
            body += f"🔹 <b>{name}</b>\n   └ {platform} • <b>{price_display}</b> ➔ <a href='{link}'>View</a>\n\n"
        else:
            body += f"🔹 <b>{name}</b>\n   └ <i>No phones matched active price filters</i>\n\n"
            
    footer = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <i>Radar scanning 24/7. Next summary in 30 mins.</i>"
    )
    send_telegram_raw(header + body + footer)

# ==================== PARSER & VALIDATOR ====================
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

# ==================== MAIN AUTOMATION LOOP ====================
def scanner_loop():
    print("Master Sentinel Loop active. Continuous scanning with 30-min dashboard cycle...", flush=True)
    alerted_glitch_links = set()
    session = cureq.Session(impersonate="chrome120")
    
    last_dashboard_time = 0
    DASHBOARD_INTERVAL = 1800  # 30 minutes in seconds

    while True:
        try:
            dashboard_summary = []
            current_time = time.time()
            should_send_dashboard = (current_time - last_dashboard_time) >= DASHBOARD_INTERVAL

            for rule in MASTER_TARGET_RULES:
                glitch_threshold = rule["glitch_max"]
                lowest_item = None

                # 1. Sweep Flipkart
                fk_items = scan_flipkart_feed(session, rule["flipkart_url"], rule)
                for item in fk_items:
                    p = item["price"]
                    if p > 0:
                        if lowest_item is None or p < lowest_item["price"]:
                            lowest_item = item
                        # Real-time glitch trigger
                        if p <= glitch_threshold and item["link"] not in alerted_glitch_links:
                            alerted_glitch_links.add(item["link"])
                            print(f"[GLITCH DROP] {item['title']} @ ₹{p:,} on Flipkart", flush=True)
                            send_instant_glitch_alert(item["title"], p, "Flipkart", item["link"])
                time.sleep(1)

                # 2. Sweep Amazon
                amz_items = scan_amazon_feed(session, rule["amazon_url"], rule)
                for item in amz_items:
                    p = item["price"]
                    if p > 0:
                        if lowest_item is None or p < lowest_item["price"]:
                            lowest_item = item
                        # Real-time glitch trigger
                        if p <= glitch_threshold and item["link"] not in alerted_glitch_links:
                            alerted_glitch_links.add(item["link"])
                            print(f"[GLITCH DROP] {item['title']} @ ₹{p:,} on Amazon", flush=True)
                            send_instant_glitch_alert(item["title"], p, "Amazon", item["link"])
                time.sleep(1)

                # Record data for periodic summary
                if lowest_item:
                    dashboard_summary.append({
                        "name": rule["name"],
                        "price": lowest_item["price"],
                        "platform": lowest_item["platform"],
                        "link": lowest_item["link"]
                    })
                else:
                    dashboard_summary.append({
                        "name": rule["name"],
                        "price": 0,
                        "platform": "N/A",
                        "link": "#"
                    })

            # Send periodic dashboard table every 30 minutes
            if should_send_dashboard:
                send_gui_dashboard(dashboard_summary)
                last_dashboard_time = current_time
                print("Dashboard summary delivered to Telegram.", flush=True)

        except Exception as e:
            print(f"[!] Scanner loop error: {e}", flush=True)

        time.sleep(60)

if __name__ == "__main__":
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()
    scanner_loop()
