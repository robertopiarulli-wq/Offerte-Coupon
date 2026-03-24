import os
import requests
import feedparser
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE SECRET ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

# --- 1. BLACKLIST POTENZIATA (Addio detersivi e creme) ---
BLACKLIST = [
    "detersivo", "shampoo", "crema", "siero", "panni", "ammorbidente", "dentifricio",
    "mascara", "trucco", "cosmetici", "smalto", "bagnoschiuma", "solare", "pannolini",
    "concorso", "vinci", "estrazione", "partecipa", "gioca", "instant win", "regolamento",
    "provami gratis", "rimborso", "cashback" # Spesso sono rimborsi complessi, li togliamo?
]

# --- 2. WHITELIST BRAND (Cosa vogliamo davvero) ---
TECH_TARGETS = [
    "apple", "iphone", "samsung", "galaxy", "sony", "ps5", "nintendo", "xbox", 
    "dyson", "lg", "asus", "xiaomi", "laptop", "pc", "monitor", "tv", "tablet", 
    "cuffie", "lego", "robot", "scopa elettrica"
]

RSS_FEEDS = {
    "ScontoMaggio": "https://www.scontomaggio.com/feed/",
    "Omaggiomania": "https://www.omaggiomania.com/feed/",
    "Pepper_Nuovi": "https://www.pepper.it/rss/nuovi",
    "HDBlog": "https://www.hdblog.it/offerte/feed/"
}

def send_alert(tipo, titolo, link, fonte):
    # Personalizziamo l'icona in base al contenuto
    icona = "🚨" if "ERRORE" in tipo else "🔥" if "TECH" in tipo else "🎁"
    msg = f"{icona} *{tipo}*\n\n📦 {titolo}\n📡 Fonte: {fonte}\n\n🔗 [APRI OFFERTA]({link})"
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
    print("📡 Scansione Radar v3.2...")
    for nome, url_feed in RSS_FEEDS.items():
        feed = feedparser.parse(url_feed)
        for entry in feed.entries:
            t = entry.title.lower()
            
            # FILTRO 1: Salta se è in Blacklist
            if any(b in t for b in BLACKLIST):
                continue
            
            tipo = None
            
            # FILTRO 2: Cerca Errori o Omaggi di valore
            if "errore" in t or "follia" in t:
                tipo = "🚨 ERRORE PREZZO"
            elif any(x in t for x in ["0€", "gratis", "omaggio"]):
                # Se è gratis, lo prendiamo solo se non è un detersivo (già filtrato da blacklist)
                tipo = "🎁 OMAGGIO / CAMPIONE"
            elif any(brand in t for brand in TECH_TARGETS):
                # Se contiene un brand della nostra lista tech
                tipo = "🔥 AFFARE TECH"
            
            if tipo:
                check_db_and_save(entry.title, entry.link, tipo, nome)

def scan_amazon_warehouse():
    print("📦 Scansione Amazon Warehouse (Filtro Brand)...")
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        for p in products[:15]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            
            # Prendiamo solo se è un brand tech desiderato
            if any(brand in title.lower() for brand in TECH_TARGETS):
                check_db_and_save(title, link, "📦 AMAZON WAREHOUSE", "Amazon")
    except Exception as e:
        print(f"Errore Amazon: {e}")

if __name__ == "__main__":
    scan_rss()
    scan_amazon_warehouse()
    print("✅ Ciclo Radar v3.2 Completato.")
