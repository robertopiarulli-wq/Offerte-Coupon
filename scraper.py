import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client
import time

# Configurazione Supabase
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")
sb = create_client(URL_SB, KEY_SB)

def esegui_scraping():
    home_url = "https://www.podopiu.com/negozio/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 Avvio Scraper Intelligente...")
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Prende le categorie principali
    categorie = soup.find_all('li', class_='product-category')
    
    # Set per evitare duplicati e prodotti correlati
    prodotti_gia_fatti = set()

    for cat in categorie:
        nome_cat = cat.find('h2').text.split('(')[0].strip()
        link_cat = cat.find('a')['href']
        print(f"\n📂 Analisi Categoria: {nome_cat}")

        res_c = requests.get(link_cat, headers=headers)
        soup_c = BeautifulSoup(res_c.text, 'html.parser')
        
        # Selettore mirato: solo i prodotti nella griglia principale
        prodotti = soup_c.select('ul.products li.product > a:first-child')

        for p_link in prodotti:
            url_prodotto = p_link['href']
            
            # Salta se lo abbiamo già scansionato in questo run
            if url_prodotto in prodotti_gia_fatti:
                continue
            
            prodotti_gia_fatti.add(url_prodotto)

            try:
                # Entriamo nella scheda prodotto
                res_p = requests.get(url_prodotto, headers=headers)
                soup_p = BeautifulSoup(res_p.text, 'html.parser')
                
                # Estrazione dati SKU e Descrizione
                sku_tag = soup_p.find('span', class_='sku')
                sku = sku_tag.text.strip() if sku_tag else "ND-" + url_prodotto.split('/')[-2][:10]
                
                nome = soup_p.find('h1', class_='product_title').text.strip()
                img = soup_p.find('img', class_='wp-post-image')['src']
                
                desc_tag = soup_p.find('div', class_='woocommerce-product-details__short-description')
                desc_text = desc_tag.get_text(separator=' ').strip() if desc_tag else ""

                data = {
                    "codice": sku,
                    "nome": nome,
                    "immagine_url": img,
                    "descrizione": desc_text,
                    "categoria": nome_cat
                }
                
                # Salva su Supabase (Upsert aggiorna se il codice esiste già)
                sb.table("prodotti").upsert(data, on_conflict="codice").execute()
                print(f" ✅ OK: {nome} [{sku}]")
                
                # Piccola pausa per non sovraccaricare il server
                time.sleep(0.5)

            except Exception as e:
                print(f" ❌ Errore su {url_prodotto}: {e}")
                continue

    print("\n✨ Scansione completata con successo!")

if __name__ == "__main__":
    esegui_scraping()
