import os, requests, feedparser, datetime
from bs4 import BeautifulSoup
from supabase import create_client, Client

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}

# --- TARGET ESPANSO (Maiuscole/Minuscole gestite in automatico) ---
GOLD_TARGETS = ["apple", "iphone", "ipad", "macbook", "samsung", "galaxy", "sony", "ps5", "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "msi", "rtx", "nvidia", "hp", "lenovo", "dell", "logitech", "bose", "sonos", "dji", "garmin", "laptop", "monitor", "tv", "smartphone", "tablet", "cuffie", "smartwatch", "bici", "monopattino"]

# --- FONTI ---
RSS_FEEDS = {
    "Pepper_Elettronica": "https://www.pepper.it/rss/elettronica",
    "Pepper_Informatica": "https://www.pepper.it/rss/informatica",
    "HDBlog": "https://www.hdblog.it/offerte/feed/",
    "Hardware_Upgrade": "https://www.hwupgrade.it/rss_offerte.xml"
}

def send_alert(tipo, titolo, link, fonte, silent=False):
    icona = "🚨" if "ERRORE" in tipo else "💎" if "TARGET" in tipo else "🤖"
    msg = f"{icona} *{tipo}*\n\n📦 {titolo}\n📡 Fonte: {fonte}\n\n🔗 [VEDI ORA]({link})"
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_notification": silent})

def check_db_and_save(titolo, url, tipo, fonte):
    try:
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            supabase.table("offerte").insert({"titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte}).execute()
            send_alert(tipo, titolo, url, fonte)
            return True
    except Exception as e: print(f"Errore DB: {e}")
    return False

def run_scanner():
    print("🛰️ Avvio Scansione Totale v3.8...")
    # Messaggio di Status Silenzioso (per sapere che sta girando)
    # send_alert("STATUS", "Radar in scansione...", "http://github.com", "System", silent=True)
    
    found_count = 0
    for nome, url_feed in RSS_FEEDS.items():
        feed = feedparser.parse(url_feed)
        print(f"--- Analizzando {nome} ({len(feed.entries)} articoli) ---")
        for entry in feed.entries:
            t = entry.title.lower()
            
            tipo = None
            # 1. ERRORI (Priorità)
            if any(x in t for x in ["errore", "follia", "baco", "0€", "gratis", "bug"]):
                tipo = "🚨 ERRORE/OFFERTA PAZZA"
            # 2. BRAND ORO (Sensibilità massima)
            elif any(brand in t for brand in GOLD_TARGETS):
                tipo = "💎 TARGET RILEVATO"
            # 3. SCONTI FORTI
            elif any(s in t for s in ["70%", "80%", "90%", "fuori tutto"]):
                tipo = "🔥 SCONTO BOMBA"
            
            if tipo:
                if check_db_and_save(entry.title, entry.link, tipo, nome):
                    found_count += 1
    
    print(f"✅ Scansione completata. Nuovi messaggi inviati: {found_count}")

if __name__ == "__main__":
    run_scanner()
    # Amazon Warehouse rapido
    try:
        res = requests.get("https://www.amazon.it/s?k=elettronica&i=warehouse-deals", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for p in soup.find_all('div', {'data-component-type': 's-search-result'})[:5]:
            title = p.find('h2').text.strip()
            link = "https://www.amazon.it" + p.find('a')['href'].split('?')[0]
            if any(brand in title.lower() for brand in GOLD_TARGETS):
                check_db_and_save(title, link, "📦 WAREHOUSE GOLD", "Amazon")
    except: pass
