import os
import requests
import feedparser
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE SECRET (DA GITHUB) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

# --- PARAMETRI DEL RADAR ---
BLACKLIST = ["usato", "ricondizionato", "custodia", "cover", "pellicola", "vetro", "concorso", "estrazione"]
RSS_FEEDS = {
    "ScontoMaggio": "https://www.scontomaggio.com/feed/",
    "Omaggiomania": "https://www.omaggiomania.com/feed/",
    "Pepper_Nuovi": "https://www.pepper.it/rss/nuovi",
    "HDBlog": "https://www.hdblog.it/offerte/feed/"
}

# --- FUNZIONI CORE ---

def send_alert(tipo, titolo, prezzo, link, fonte):
    """Invia la notifica formattata su Telegram"""
    icona = "🚨" if "ERRORE" in tipo else "🎁" if "CAMPIONE" in tipo else "🔥"
    prezzo_display = f"{prezzo}€" if prezzo > 0 else "GRATIS / TESTER"
    
    msg = (
        f"{icona} *{tipo}*\n\n"
        f"📦 *{titolo}*\n"
        f"💰 Prezzo: {prezzo_display}\n"
        f"📡 Fonte: {fonte}\n\n"
        f"🔗 [VAI ALL'AFFARE]({link})"
    )
    
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Errore invio TG: {e}")

def check_db_and_save(titolo, url, tipo, fonte, prezzo=0):
    """Controlla se l'offerta è nuova e la salva"""
    try:
        # Verifica se l'URL esiste già
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            # Inserimento
            supabase.table("offerte").insert({
                "titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte, "prezzo": prezzo
            }).execute()
            # Alert
            send_alert(tipo, titolo, prezzo, url, fonte)
            return True
    except Exception as e:
        print(f"Errore Database: {e}")
    return False

def scan_rss():
    print("📡 Scansione Feed RSS...")
    for nome, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            t = entry.title.lower()
            if any(key in t for key in ["errore", "0€", "gratis", "omaggio", "minimo storico", "tester"]):
                if not any(b in t for b in BLACKLIST):
                    tipo = "ERRORE PREZZO" if "errore" in t else "CAMPIONE/AFFARE"
                    check_db_and_save(entry.title, entry.link, tipo, nome)

def scan_amazon_warehouse():
    print("📦 Scansione Amazon Warehouse...")
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for p in products[:10]: # Analizziamo i primi 10 per sicurezza
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            # Filtro brand grossi per Warehouse
            if any(brand in title.lower() for brand in ["apple", "samsung", "sony", "ps5", "nintendo", "dyson"]):
                check_db_and_save(title, link, "📦 WAREHOUSE GEM", "Amazon", 0)
    except Exception as e:
        print(f"Errore Amazon: {e}")

# --- ESECUZIONE ---
if __name__ == "__main__":
    scan_rss()
    scan_amazon_warehouse()
    print("✅ Ciclo completato.")
