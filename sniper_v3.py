import os, requests, datetime
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

# --- TARGET & BLACKLIST ---
BLACKLIST = ["detersivo", "shampoo", "crema", "siero", "panni", "carta", "conto", "hype"]
GOLD_TARGETS = ["apple", "iphone", "ipad", "macbook", "samsung", "galaxy", "sony", "ps5", "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "msi", "rtx", "nvidia", "laptop", "monitor", "tv", "smartphone"]

def send_alert(tipo, titolo, link, fonte):
    icona = "🚨" if "ERRORE" in tipo else "💎"
    msg = f"{icona} *{tipo}*\n\n📦 {titolo}\n📡 Fonte: {fonte}\n\n🔗 [VEDI ORA]({link})"
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def check_db_and_save(titolo, url, tipo, fonte):
    try:
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            supabase.table("offerte").insert({"titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte}).execute()
            send_alert(tipo, titolo, url, fonte)
            return True
    except: return False

def scrape_pepper():
    print("🌶️ Scraping Pepper Elettronica...")
    url = "https://www.pepper.it/nuovo/elettronica"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Troviamo tutti i titoli delle offerte
        articles = soup.find_all('strong', class_='thread-title')
        print(f"--- Trovati {len(articles)} potenziali articoli su Pepper ---")
        
        for art in articles:
            titolo = art.text.strip()
            t = titolo.lower()
            link_tag = art.find('a')
            if not link_tag: continue
            link = "https://www.pepper.it" + link_tag['href'].split('?')[0]

            if any(b in t for b in BLACKLIST): continue
            
            tipo = None
            if any(x in t for x in ["errore", "follia", "0€", "bug"]): tipo = "🚨 ERRORE"
            elif any(brand in t for brand in GOLD_TARGETS): tipo = "💎 TARGET GOLD"
            elif any(s in t for s in ["70%", "80%", "90%"]): tipo = "🔥 SCONTO"

            if tipo:
                check_db_and_save(titolo, link, tipo, "Pepper Web")
    except Exception as e: print(f"Errore Pepper: {e}")

def scrape_hdblog():
    print("📱 Scraping HDBlog...")
    url = "https://www.hdblog.it/offerte/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.find_all('a', class_='title')
        print(f"--- Trovati {len(articles)} articoli su HDBlog ---")
        for art in articles:
            titolo = art.text.strip()
            link = art['href']
            if any(brand in titolo.lower() for brand in GOLD_TARGETS):
                check_db_and_save(titolo, link, "💎 TARGET GOLD", "HDBlog Web")
    except: pass

if __name__ == "__main__":
    scrape_pepper()
    scrape_hdblog()
