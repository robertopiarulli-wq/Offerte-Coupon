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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

# --- FILTRI STRATEGICI ---
BLACKLIST = [
    "detersivo", "shampoo", "crema", "siero", "panni", "ammorbidente", "dentifricio",
    "mascara", "trucco", "cosmetici", "smalto", "bagnoschiuma", "solare", "pannolini",
    "concorso", "vinci", "estrazione", "partecipa", "gioca", "instant win", "regolamento"
]

TECH_TARGETS = [
    "apple", "iphone", "ipad", "macbook", "samsung", "galaxy", "sony", "ps5", "playstation",
    "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "xiaomi", "laptop", 
    "rtx", "nvidia", "canon", "nikon", "dj", "bose", "sonos", "garmin"
]

RSS_FEEDS = {
    "ScontoMaggio": "https://www.scontomaggio.com/feed/",
    "Omaggiomania": "https://www.omaggiomania.com/feed/",
    "Pepper_Nuovi": "https://www.pepper.it/rss/nuovi",
    "HDBlog": "https://www.hdblog.it/offerte/feed/"
}

def send_alert(tipo, titolo, link, fonte, is_test=False):
    if is_test:
        msg = f"🤖 *Radar Status*: Operativo\n⏱️ {datetime.datetime.now().strftime('%H:%M')}\n✅ Scansione fonti completata."
    else:
        icona = "🚨" if "ERRORE" in tipo else "🔥" if "TECH" in tipo else "🎁"
        msg = f"{icona} *{tipo}*\n\n📦 {titolo}\n📡 Fonte: {fonte}\n\n🔗 [APRI ORA]({link})"
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

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

def scan_rss():
    print("📡 Scansione Radar v3.3...")
    found_something = False
    for nome, url_feed in RSS_FEEDS.items():
        feed = feedparser.parse(url_feed)
        for entry in feed.entries:
            t = entry.title.lower()
            if any(b in t for b in BLACKLIST): continue
            
            tipo = None
            # 1. Errori/Bug
            if any(x in t for x in ["errore", "follia", "baco", "prezzaccio"]):
                tipo = "🚨 ERRORE PREZZO"
            # 2. Omaggi Reali (Non cosmetici)
            elif any(x in t for x in ["0€", "gratis", "omaggio", "tester"]):
                tipo = "🎁 OMAGGIO VALORE"
            # 3. Target Tech
            elif any(brand in t for brand in TECH_TARGETS):
                tipo = "🔥 TECH TARGET"
            # 4. Sconti Massicci
            elif any(s in t for s in ["70%", "80%", "90%", "fuori tutto"]):
                tipo = "💣 SCONTO BOMBA"
            
            if tipo:
                if check_db_and_save(entry.title, entry.link, tipo, nome):
                    found_something = True
    return found_something

def scan_amazon_warehouse():
    print("📦 Scansione Warehouse...")
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        for p in products[:15]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            if any(brand in title.lower() for brand in TECH_TARGETS):
                check_db_and_save(title, link, "📦 WAREHOUSE TECH", "Amazon")
    except: pass

if __name__ == "__main__":
    # Esegue la scansione
    something_new = scan_rss()
    scan_amazon_warehouse()
    
    # Log di sistema su GitHub
    print(f"✅ Ciclo Completato. Nuove offerte inviate: {something_new}")
