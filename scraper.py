import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Configurazione Ambiente
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
sb = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://www.podopiu.com/negozio/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("Avvio scansione PodoPiù...")
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Individua le categorie
    categorie = soup.find_all('li', class_='product-category')
    
    for cat in categorie:
        nome_cat = cat.find('h2').text.split('(')[0].strip()
        link_cat = cat.find('a')['href']
        print(f"\n📂 Categoria: {nome_cat}")

        res_c = requests.get(link_cat, headers=headers)
        soup_c = BeautifulSoup(res_c.text, 'html.parser')
        prodotti = soup_c.find_all('li', class_='product')

        for p in prodotti:
            try:
                nome = p.find('h2').text.strip()
                img = p.find('img')['src'] if p.find('img') else ""
                link_p = p.find('a')['href']
                
                # Entriamo nella scheda prodotto per dettagli
                res_p = requests.get(link_p, headers=headers)
                soup_p = BeautifulSoup(res_p.text, 'html.parser')
                
                sku = soup_p.find('span', class_='sku').text.strip() if soup_p.find('span', class_='sku') else "ND-" + nome[:3].upper()
                desc_tag = soup_p.find('div', class_='woocommerce-product-details__short-description')
                desc_text = desc_tag.text.strip() if desc_tag else "Descrizione disponibile sul sito."

                p_data = {
                    "codice": sku,
                    "nome": nome,
                    "immagine_url": img,
                    "descrizione": desc_text,
                    "categoria": nome_cat
                }
                
                # Salvataggio con gestione conflitti
                sb.table("prodotti").upsert(p_data, on_conflict="codice").execute()
                print(f" ✅ {nome} (SKU: {sku})")
                
            except Exception as e:
                print(f" ❌ Errore su un prodotto: {e}")
                continue

if __name__ == "__main__":
    esegui_scraping()
