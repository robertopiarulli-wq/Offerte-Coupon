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

# Header corazzati per non essere rimbalzati dai siti
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
}

# --- 1. BLACKLIST (Eliminiamo la fuffa e i servizi bancari) ---
BLACKLIST = [
    "detersivo", "shampoo", "crema", "siero", "panni", "ammorbidente", "dentifricio",
    "mascara", "trucco", "cosmetici", "smalto", "bagnoschiuma", "solare", "pannolini",
    "concorso", "vinci", "estrazione", "regolamento", "carta", "conto", "hype", "revolut", "bonus"
]

# --- 2. GOLD TARGETS (Appena legge uno di questi, spara la notifica) ---
GOLD_TARGETS = [
    "apple", "iphone", "ipad", "macbook", "airpods", "samsung", "galaxy", "sony", "ps5", 
    "playstation", "nintendo", "switch", "xbox", "dyson", "lg", "oled", "asus", "rog", 
    "msi", "rtx", "nvidia", "hp", "lenovo", "dell", "logitech", "razer", "bose", "sonos", 
    "canon", "nikon", "dji", "garmin", "laptop", "monitor", "tv", "smartphone", "tablet",
    "cuffie", "smartwatch", "bici", "monopattino"
]

# --- 3. FONTI SOLO TECH ---
RSS_FEEDS = {
    "Pepper_Elettronica": "https://www.pepper.it/rss/elettronica",
    "Pepper_Informatica": "https://www.pepper.it/rss/informatica",
    "HDBlog_Offerte": "https://www.hdblog.it/offerte/feed/",
    "Hardware_Upgrade": "https://www.hwupgrade.it/rss_offerte.xml"
}

def send_alert(tipo, titolo, link, fonte):
    icona = "🚨" if "ERRORE" in tipo else "💎" if "GOLD" in tipo else "🔥"
    msg = (
        f"{icona} *{tipo}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 *{titolo}*\n"
        f"📡 Fonte: {fonte}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 [APRI OFFERTA ORA]({link})"
    )
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def check_db_and_save(titolo, url, tipo, fonte):
    try:
        # Controlla se l'offerta esiste già
        res = supabase.table("offerte").select("*").eq("url", url).execute()
        if not res.data:
            supabase.table("offerte").insert({"titolo": titolo, "url": url, "tipo": tipo, "fonte": fonte}).execute()
            send_alert(tipo, titolo, url, fonte)
            return True
    except Exception as e:
        print(f"Errore Database: {e}")
    return False

def run_scanner
