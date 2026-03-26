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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}

# --- 1. BLACKLIST (Mantenuta e rinforzata per sicurezza) ---
BLACKLIST = [
    "detersivo", "shampoo", "crema", "siero", "panni", "ammorbidente", "dentifricio",
    "mascara", "trucco", "cosmetici", "smalto", "bagnoschiuma", "solare", "pannolini",
    "concorso", "vinci", "estrazione", "partecipa", "gioca", "instant win", "regolamento"
]

# --- 2. GOLD TARGETS (I Grandi Nomi che cerchi) ---
GOLD_TARGETS = [
    "apple", "iphone", "ipad", "macbook", "airpods", "samsung", "galaxy", "sony", "ps5", 
    "playstation", "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "rog", 
    "msi", "rtx", "nvidia", "hp", "lenovo", "dell", "logitech", "razer", "bose", "sonos", 
    "canon", "nikon", "dji", "garmin", "laptop", "monitor", "tv"
]

# --- 3. FONTI STRATEGICHE (Sostituite quelle "povere" con quelle Tech) ---
RSS_FEEDS = {
    "Pepper_Elettronica": "https://www.pepper.it/rss/elettronica",
    "Pepper_Informatica": "https://www.pepper.it/rss/informatica",
    "HDBlog_Offerte": "https://www.hdblog.it/offerte/feed/",
    "Hardware_Upgrade": "https://www.hwupgrade.it/rss_offerte.xml"
}

def send_alert(tipo, titolo, link, fonte, is_test=False):
    if is_test:
        msg = f"🤖 *Radar Status*: Operativo\n⏱️ {datetime.datetime.now().strftime('%H:%M')}\n✅ Scansione fonti Gold completata."
    else:
        # Messaggio più visibile per i Grandi Affari
        icona = "🚨" if "ERRORE" in tipo else "💎" if "GOLD" in tipo else "💣"
        msg = (
            f"{icona} *{tipo}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📦 *{titolo}*\n"
            f"📡 Fonte: {fonte}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔥 [ACCHIAPPA L'AFFARE]({link})"
        )
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Errore invio TG: {e}")

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
    print("🚀 Scansione Radar Gold v3.5...")
    found_something = False
    for nome, url_feed in RSS_FEEDS.items():
        feed = feedparser.parse(url_feed)
        for entry in feed.entries:
            t = entry.title.lower()
            
            # Filtro sicurezza
            if any(b in t for b in BLACKLIST): continue
            
            tipo = None
            # Logica di intercettazione Grandi Affari
            if any(x in t for x in ["errore", "follia", "baco", "0€", "gratis"]):
                tipo = "🚨 ERRORE PREZZO / BUG"
            elif any(brand in t for brand in GOLD_TARGETS):
                # Se è un grande brand e c'è una parola "affare"
                if any(ok in t for ok in ["sconto", "minimo", "offerta", "ribasso", "crollato", "%"]):
                    tipo = "💎 GOLD TECH TARGET"
            elif any(s in t for s in ["80%", "90%", "fuori tutto"]):
                tipo = "💣 SCONTO MASSICCIO"
            
            if tipo:
                if check_db_and_save(entry.title, entry.link, tipo, nome):
                    found_something = True
    return found_something

def scan_amazon_warehouse():
    print("📦 Scansione Amazon Warehouse...")
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        for p in products[:15]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            if any(brand in title.lower() for brand in GOLD_TARGETS):
                check_db_and_save(title, link, "📦 WAREHOUSE GOLD", "Amazon Warehouse")
    except: pass

if __name__ == "__main__":
    # Esecuzione Radar
    new_findings = scan_rss()
    scan_amazon_warehouse()
    
    # Self-Test (Opzionale: manda un segnale alle 8 del mattino)
    current_hour = datetime.datetime.now().hour
    if current_hour == 8:
        send_alert(None, None, None, None, is_test=True)
        
    print(f"✅ Ciclo Completato. Nuove bombe inviate: {new_findings}")
