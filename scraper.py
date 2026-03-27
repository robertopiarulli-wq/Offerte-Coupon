import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://www.podopiu.com/negozio/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. Trova le categorie (nel sito PodoPiù sono nei box 'product-category')
    categorie_items = soup.find_all('li', class_='product-category')
    
    for cat in categorie_items:
        nome_categoria = cat.find('h2').text.strip()
        link_categoria = cat.find('a')['href']
        
        print(f"Entro in: {nome_categoria}...")
        
        res_cat = requests.get(link_categoria, headers=headers)
        soup_cat = BeautifulSoup(res_cat.text, 'html.parser')
        
        # 2. Trova i prodotti nella pagina della categoria
        # In questo sito i prodotti sono dentro 'li' con classe 'product'
        items = soup_cat.find_all('li', class_='product')
        
        for item in items:
            try:
                # Estrazione dati specifica per PodoPiù
                nome = item.find('h2').text.strip()
                img = item.find('img')['src']
                # Il codice spesso è negli attributi o nel testo, qui generiamo uno slug unico
                codice_generato = nome.replace(" ", "-").upper()[:15] 
                
                p_data = {
                    "codice": codice_generato,
                    "nome": nome,
                    "immagine_url": img,
                    "descrizione": "Visualizza dettagli sul sito",
                    "categoria": nome_categoria
                }
                
                # Upsert su Supabase
                supabase.table("prodotti").upsert(p_data, on_conflict="codice").execute()
            except Exception as e:
                print(f"Errore prodotto: {e}")

if __name__ == "__main__":
    esegui_scraping()
