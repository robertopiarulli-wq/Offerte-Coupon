import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Configurazione Supabase
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://share.google/2a1HjpodGQ2SYBLZe" 
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. Trova i link delle categorie (Verifica la classe 'category-link' sul sito reale!)
    categorie_links = soup.find_all('a', class_='category-link') 
    
    for cat in categorie_links:
        nome_categoria = cat.text.strip()
        link_categoria = cat['href']
        
        if not link_categoria.startswith('http'):
            link_categoria = "https://tuo-sito-base.com" + link_categoria

        print(f"Scansione categoria: {nome_categoria}...")
        
        res_cat = requests.get(link_categoria, headers=headers)
        soup_cat = BeautifulSoup(res_cat.text, 'html.parser')
        
        # 2. Estrai i prodotti (Verifica la classe 'product-card')
        items = soup_cat.find_all('div', class_='product-card')
        
        for item in items:
            try:
                p_data = {
                    "codice": item.find('span', class_='codice-articolo').text.strip() if item.find('span', class_='codice-articolo') else "SNC-" + item.find('h3').text[:3].upper(), 
                    "nome": item.find('h3').text.strip(),
                    "immagine_url": item.find('img')['src'] if item.find('img') else "",
                    "descrizione": item.find('p').text.strip() if item.find('p') else "",
                    "categoria": nome_categoria 
                }
                
                # 3. Upsert basato su CODICE
                supabase.table("prodotti").upsert(p_data, on_conflict="codice").execute()
                
            except Exception as e:
                print(f"Errore su un prodotto: {e}")

if __name__ == "__main__":
    esegui_scraping()
