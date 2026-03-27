import os
import requests
import json
from bs4 import BeautifulSoup
from supabase import create_client

# Configurazione Supabase (usando i Secrets di GitHub)
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://share.google/2a1HjpodGQ2SYBLZe" # La tua pagina d'ingresso
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. Trova tutte le categorie nella prima pagina
    # (Qui devi indicare al bot come riconoscere i link delle categorie)
    categorie_links = soup.find_all('a', class_='category-link') 
    
    for cat in categorie_links:
        nome_categoria = cat.text.strip()
        link_categoria = cat['href']
        
        # Se il link è relativo, aggiungi il dominio
        if not link_categoria.startswith('http'):
            link_categoria = "https://tuo-sito-base.com" + link_categoria

        print(f"Scansione categoria: {nome_categoria}...")
        
        # 2. Entra nella pagina della categoria
        res_cat = requests.get(link_categoria, headers=headers)
        soup_cat = BeautifulSoup(res_cat.text, 'html.parser')
        
        # 3. Estrai i prodotti di questa specifica categoria
        items = soup_cat.find_all('div', class_='product-card')
        
        for item in items:
            p_data = {
                "nome": item.find('h3').text.strip(),
                "immagine_url": item.find('img')['src'],
                "descrizione": item.find('p').text.strip(),
                "categoria": nome_categoria # Assegna la categoria corrente
            }
            # Salva su Supabase (Upsert aggiorna se esiste già il nome)
            supabase.table("prodotti").upsert(p_data, on_conflict="nome").execute()

if __name__ == "__main__":
    esegui_scraping()
