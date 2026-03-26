import os, requests, datetime
from supabase import create_client, Client

# --- CONFIGURAZIONE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# URL API DI PEPPER (Quello che usa l'App)
PEPPER_API_URL = "https://www.pepper.it/api/v1/threads/new"

HEADERS = {
    "User-Agent": "Pepper-App/1.0",
    "Accept": "application/json"
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

def run_api_scan():
    print("🛰️ Scansione API Pepper v4.2...")
    try:
        # Chiediamo i dati in formato JSON (niente HTML da pulire)
        res = requests.get(PEPPER_API_URL, headers=HEADERS, timeout=20)
        data = res.json()
        
        # Le offerte sono nella lista 'data' del JSON
        items = data.get('data', [])
        print(f"--- Ricevuti {len(items)} oggetti tech da Pepper ---")
        
        found_count = 0
        for item in items:
            titolo = item.get('title', '')
            t = titolo.lower()
            # Pulizia link
            link = item.get('url', '')
            
            if any(b in t for b in BLACKLIST): continue
            
            tipo = None
            if any(x in t for x in ["errore", "follia", "0€", "bug"]): tipo = "🚨 ERRORE"
            elif any(brand in t for brand in GOLD_TARGETS): tipo = "💎 TARGET GOLD"
            elif any(s in t for s in ["70%", "80%", "90%"]): tipo = "🔥 SCONTO"

            if tipo:
                if check_db_and_save(titolo, link, tipo, "Pepper API"):
                    found_count += 1
        
        print(f"✅ Nuovi affari inviati: {found_count}")
    except Exception as e:
        print(f"❌ Errore API: {e}")

if __name__ == "__main__":
    run_api_scan()
