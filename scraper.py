import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Prende le chiavi dai Secret di GitHub
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    url = "https://share.google/2a1HjpodGQ2SYBLZe"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Esempio di logica per estrarre i box prodotto
    items = soup.find_all('div', class_='product-card') # Da affinare su HTML reale
    
    for item in items:
        p_data = {
            "nome": item.find('h3').text.strip(),
            "immagine_url": item.find('img')['src'],
            "descrizione": item.find('p').text.strip(),
            "categoria": "Feltri e protezioni"
        }
        # Upsert evita duplicati basandosi sul nome
        supabase.table("prodotti").upsert(p_data, on_conflict="nome").execute()

if __name__ == "__main__":
    esegui_scraping()
