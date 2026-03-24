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

# --- PARAMETRI RADAR POTENZIATI ---
# Eliminano concorsi, estrazioni e fuffa
# BLACKLIST = [
    "usato", "ricondizionato", "custodia", "cover", "pellicola", "vetro", 
    "concorso", "estrazione", "vinci", "partecipa", "gioca", "instant win", 
    "sorteggio", "premi in palio", "scadenza", "regolamento", "invita", "estrazioni"
]

# Brand da monitorare su Amazon Warehouse (Aggiunti Samsung, LG, Asus, etc.)
TECH_BRANDS = [
    "apple", "samsung", "sony", "ps5", "nintendo", "dyson", "lg", 
    "asus", "bosch", "lego", "logitech", "hp", "lenovo", "xiaomi"
]

RSS_FEEDS = {
    "ScontoMaggio": "https://www.scontomaggio.com/feed/",
    "Omaggiomania": "https://www.omaggiomania.com/feed/",
    "Pepper_Nuovi": "https://www.pepper.it/rss/nuovi",
    "HDBlog": "https://www.hdblog.it/offerte/feed/"
}

# --- FUNZIONI CORE ---

def send_alert(tipo, titolo, prezzo, link, fonte):
    icona = "🚨" if "ERRORE" in tipo else "🎁" if "OMAGGIO" in tipo else "🧪" if "TESTER" in tipo else "📦"
    prezzo_display = f"{prezzo}€" if prezzo > 0 else "GRATIS / DIRETTO"
    
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
        print(f"Errore TG: {e}")

def check_db_and_save(titolo, url, tipo, fonte, prezzo=0):
    try:
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            supabase.table("offerte").insert({
                "titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte, "prezzo": prezzo
            }).execute()
            send_alert(tipo, titolo, prezzo, url, fonte)
            return True
    except Exception as e:
        print(f"Errore DB: {e}")
    return False

def scan_rss():
    print("📡 Scansione Feed RSS (Filtro Concorsi Attivo)...")
    for nome, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            t = entry.title.lower()
            
            # SALTA SE È NELLA BLACKLIST (Concorsi/Fuffa)
            if any(b in t for b in BLACKLIST):
                continue
                
            tipo = None
            # Logica Selezione Positiva
            if "errore" in t or "follia" in t:
                tipo = "🚨 ERRORE PREZZO"
            elif any(x in t for x in ["campione", "gratis", "0€", "omaggio"]):
                # Filtriamo ulteriormente per assicurarci che sia un omaggio DIRETTO
                if any(ok in t for ok in ["ricevi", "richiedi", "diretto", "arrivato", "post"]):
                    tipo = "🎁 OMAGGIO DIRETTO"
            elif "tester" in t or "provare" in t:
                tipo = "🧪 DIVENTA TESTER"

            if tipo:
                check_db_and_save(entry.title, entry.link, tipo, nome)

def scan_amazon_warehouse():
    print("📦 Scansione Amazon Warehouse (Radar Brand Attivo)...")
    # Cerchiamo direttamente nella sezione Warehouse per i brand tech
    url = "https://www.amazon.it/s?k=offerte+magazzino&i=warehouse-deals"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for p in products[:15]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a', class_='a-link-normal')['href'].split('?')[0]
            
            # Trigger solo se il titolo contiene uno dei nostri brand preferiti
            if any(brand in title.lower() for brand in TECH_BRANDS):
                check_db_and_save(title, link, "📦 WAREHOUSE TECH", "Amazon", 0)
    except Exception as e:
        print(f"Errore Amazon: {e}")

if __name__ == "__main__":
    scan_rss()
    scan_amazon_warehouse()
    print("✅ Ciclo Radar v3.1 Completato.")
