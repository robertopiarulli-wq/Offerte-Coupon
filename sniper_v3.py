import os, requests, datetime
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Header "Umani" avanzati
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9",
    "Referer": "https://www.google.it/", # Fondamentale: fingiamo di venire da Google
    "DNT": "1"
}

BLACKLIST = ["detersivo", "shampoo", "crema", "siero", "panni", "carta", "conto", "hype", "bonus"]
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

def scrape_pepper_mobile():
    print("🌶️ Tentativo su Pepper Mobile...")
    # Proviamo l'URL mobile che a volte ha meno protezioni
    url = "https://www.pepper.it/nuovo" 
    try:
        session = requests.Session()
        res = session.get(url, headers=HEADERS, timeout=30)
        print(f"Status Code Pepper: {res.status_code}") # Vediamo se ci dà 403 (Forbidden)
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Cambiamo selettore per cercare di beccare i titoli in modo più grezzo
        articles = soup.find_all(['a', 'span'], class_=lambda x: x and 'title' in x.lower())
        
        print(f"--- Trovati {len(articles)} elementi potenziali su Pepper ---")
        
        for art in articles:
            titolo = art.text.strip()
            if len(titolo) < 10: continue
            t = titolo.lower()
            
            # Se è un link, prendiamo l'href
            link = art.get('href', '#')
            if link.startswith('/'): link = "https://www.pepper.it" + link

            if any(b in t for b in BLACKLIST): continue
            
            tipo = None
            if any(x in t for x in ["errore", "follia", "0€", "bug"]): tipo = "🚨 ERRORE"
            elif any(brand in t for brand in GOLD_TARGETS): tipo = "💎 TARGET GOLD"
            
            if tipo and link != '#':
                check_db_and_save(titolo, link, tipo, "Pepper Stealth")
    except Exception as e: print(f"Errore Pepper: {e}")

if __name__ == "__main__":
    scrape_pepper_mobile()
