import os
import requests
import feedparser
import datetime
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# --- 1. BLACKLIST ---
BLACKLIST = [
    "detersivo", "shampoo", "crema", "siero", "panni", "ammorbidente", "dentifricio",
    "mascara", "trucco", "cosmetici", "smalto", "bagnoschiuma", "solare", "pannolini",
    "concorso", "vinci", "estrazione", "regolamento", "carta", "conto", "hype", "revolut", "bonus"
]

# --- 2. GOLD TARGETS ---
GOLD_TARGETS = [
    "apple", "iphone", "ipad", "macbook", "airpods", "samsung", "galaxy", "sony", "ps5", 
    "playstation", "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "rog", 
    "msi", "rtx", "nvidia", "hp", "lenovo", "dell", "logitech", "razer", "bose", "sonos", 
    "canon", "nikon", "dji", "garmin", "laptop", "monitor", "tv", "smartphone", "tablet",
    "cuffie", "smartwatch", "bici", "monopattino"
]

# --- 3. FONTI ---
RSS_FEEDS = {
    "Pepper_Elettronica": "https://www.pepper.it/rss/elettronica",
    "Pepper_Informatica": "https://www.pepper.it/rss/informatica",
    "HDBlog_Offerte": "https://www.hdblog.it/offerte/feed/",
    "Hardware_Upgrade": "https://www.hwupgrade.it/rss_offerte.xml"
}

def send_alert(tipo, titolo, link, fonte):
    icona = "🚨" if "ERRORE" in tipo else "💎" if "GOLD" in tipo else "🔥"
    msg = (
        f"{icona} *{tipo}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 *{titolo}*\n"
        f"📡 Fonte: {fonte}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 [APRI OFFERTA ORA]({link})"
    )
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def check_db_and_save(titolo, url, tipo, fonte):
    try:
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            supabase.table("offerte").insert({"titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte}).execute()
            send_alert(tipo, titolo, url, fonte)
            return True
    except Exception as e:
        print(f"Errore DB: {e}")
    return False

def run_scanner():
    print("🛰️ Avvio Scansione Forzata v3.9.1...")
    found_count = 0
    for nome, url_feed in RSS_FEEDS.items():
        try:
            response = requests.get(url_feed, headers=HEADERS, timeout=20)
            feed = feedparser.parse(response.content)
            print(f"--- {nome}: {len(feed.entries)} articoli ---")
            for entry in feed.entries:
                t = entry.title.lower()
                if any(b in t for b in BLACKLIST): continue
                
                tipo = None
                if any(x in t for x in ["errore", "follia", "baco", "0€", "bug"]):
                    tipo = "🚨 ERRORE DI PREZZO"
                elif any(brand in t for brand in GOLD_TARGETS):
                    tipo = "💎 GOLD TECH TARGET"
                elif any(s in t for s in ["70%", "80%", "90%", "fuori tutto"]):
                    tipo = "🔥 SCONTO BOMBA"
                
                if tipo:
                    if check_db_and_save(entry.title, entry.link, tipo, nome):
                        found_count += 1
        except Exception as e:
            print(f"❌ Errore su {nome}: {e}")
    print(f"✅ Nuovi messaggi: {found_count}")

def scan_amazon_warehouse():
    print("📦 Scansione Warehouse...")
    url = "https://www.amazon.it/s?k=elettronica&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        for p in products[:10]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            if any(brand in title.lower() for brand in GOLD_TARGETS):
                check_db_and_save(title, link, "📦 WAREHOUSE GOLD", "Amazon")
    except Exception as e:
        print(f"Errore Warehouse: {e}")

if __name__ == "__main__":
    run_scanner()
    scan_amazon_warehouse()
