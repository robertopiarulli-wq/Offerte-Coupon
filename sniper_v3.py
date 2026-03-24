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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

# --- PARAMETRI TEST (Blacklist svuotata per sbloccare tutto) ---
BLACKLIST = [] 

TECH_BRANDS = ["apple", "samsung", "sony", "ps5", "nintendo", "dyson", "lg", "asus", "xiaomi", "laptop", "smartphone"]

RSS_FEEDS = {
    "ScontoMaggio": "https://www.scontomaggio.com/feed/",
    "Omaggiomania": "https://www.omaggiomania.com/feed/",
    "Pepper_Nuovi": "https://www.pepper.it/rss/nuovi",
    "HDBlog": "https://www.hdblog.it/offerte/feed/"
}

def send_alert(tipo, titolo, link, fonte):
    msg = f"🎯 *{tipo}*\n\n📦 {titolo}\n📡 Fonte: {fonte}\n\n🔗 [LINK]({link})"
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
    print("📡 Test Radar RSS in corso...")
    for nome, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: # Prendiamo solo i primi 5 per ogni fonte
            t = entry.title.lower()
            # TEST: Selezioniamo quasi tutto per vedere se il bot funziona
            tipo = "TEST_RADAR"
            if "errore" in t: tipo = "🚨 POSSIBILE ERRORE"
            elif "gratis" in t or "omaggio" in t: tipo = "🎁 OMAGGIO"
            
            check_db_and_save(entry.title, entry.link, tipo, nome)

def scan_amazon_warehouse():
    print("📦 Test Amazon Warehouse...")
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        for p in products[:5]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            check_db_and_save(title, link, "📦 AMAZON TEST", "Amazon")
    except Exception as e:
        print(f"Errore Amazon: {e}")

if __name__ == "__main__":
    scan_rss()
    scan_amazon_warehouse()
    print("✅ Ciclo di TEST Completato.")
