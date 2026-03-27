import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
sb = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://www.podopiu.com/negozio/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Trova categorie reali
    categorie = soup.find_all('li', class_='product-category')
    
    for cat in categorie:
        nome_cat = cat.find('h2').text.split('(')[0].strip()
        link_cat = cat.find('a')['href']
        print(f"Scansione: {nome_cat}")

        res_c = requests.get(link_cat, headers=headers)
        soup_c = BeautifulSoup(res_c.text, 'html.parser')
        prodotti = soup_c.find_all('li', class_='product')

        for p in prodotti:
            try:
                nome = p.find('h2').text.strip()
                img = p.find('img')['src'] if p.find('img') else ""
                link_p = p.find('a')['href']
                
                # Entriamo nel prodotto per SKU e Descrizione
                res_p = requests.get(link_p, headers=headers)
                soup_p = BeautifulSoup(res_p.text, 'html.parser')
                
                sku = soup_p.find('span', class_='sku').text.strip() if soup_p.find('span', class_='sku') else "ND"
                desc = soup_p.find('div', class_='woocommerce-product-details__short-description')
                desc_text = desc.text.strip() if desc else "Dettagli sul sito"

                p_data = {
                    "codice": sku,
                    "nome": nome,
                    "immagine_url": img,
                    "descrizione": desc_text,
                    "categoria": nome_cat
                }
                sb.table("prodotti").upsert(p_data, on_conflict="codice").execute()
            except Exception as e:
                continue

if __name__ == "__main__":
    esegui_scraping()
