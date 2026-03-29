import os
import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# --- CONFIGURAZIONE CHIAVI (Fondamentale per GitHub Actions) ---
# os.environ.get cerca i "Secrets" che hai impostato su GitHub
URL_SB = os.environ.get("SUPABASE_URL")
KEY_SB = os.environ.get("SUPABASE_KEY")

# Questo controllo serve per farti capire nei log se le chiavi mancano
if not URL_SB or not KEY_SB:
    print("❌ Errore: Credenziali Supabase non trovate nelle variabili d'ambiente.")
    print("Controlla di averle inserite in Settings -> Secrets -> Actions")
    exit(1)

sb = create_client(URL_SB, KEY_SB)

def cerca_prodotto_sul_sito(codice, nome):
    search_url = f"https://www.podopiu.com/?s={codice}&post_type=product"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Se WooCommerce reindirizza alla pagina prodotto
        if soup.find('h1', class_='product_title'):
            return estrai_dati_pagina(soup)

        # Se è una lista di risultati, prendi il primo
        primo = soup.select_one('ul.products li.product a')
        if primo:
            res_p = requests.get(primo['href'], headers=headers)
            return estrai_dati_pagina(BeautifulSoup(res_p.text, 'html.parser'))
    except Exception as e:
        print(f"Errore ricerca {codice}: {e}")
    return None

def estrai_dati_pagina(soup):
    try:
        img = soup.find('img', class_='wp-post-image')['src']
        desc_tag = soup.find('div', class_='woocommerce-product-details__short-description')
        desc = desc_tag.get_text(separator=' ').strip() if desc_tag else ""
        return {"img": img, "desc": desc}
    except:
        return None

def esegui_aggiornamento():
    # Prende i prodotti dove IMG_SCRAPER è vuoto
    prodotti = sb.table("prodotti_catalogo").select("*").is_("IMG_SCRAPER", "null").execute().data
    
    print(f"🚀 Inizio elaborazione di {len(prodotti)} prodotti...")

    for p in prodotti:
        if not p['CODICE']: continue
        
        # Pulizia codice (es. da 11.60.041-F22 a 11.60.041)
        codice_puro = p['CODICE'].split('-')[0]
        print(f"🔍 Cerco: {codice_puro}...")
        
        dati = cerca_prodotto_sul_sito(codice_puro, p['NOME'])
        
        if dati:
            # Aggiorna il prodotto principale
            sb.table("prodotti_catalogo").update({
                "IMG_SCRAPER": dati['img'],
                "DESCRIZIONE_SCRAPER": dati['desc']
            }).eq("id", p['id']).execute()
            
            # Aggiorna i correlati se presenti
            if p['GRUPPO_CORRELATI']:
                sb.table("prodotti_catalogo").update({
                    "IMG_SCRAPER": dati['img'],
                    "DESCRIZIONE_SCRAPER": dati['desc']
                }).eq("GRUPPO_CORRELATI", p['GRUPPO_CORRELATI']).execute()
                print(f" ✅ Gruppo {p['GRUPPO_CORRELATI']} OK")
            else:
                print(f" ✅ Singolo OK")
        else:
            print(f" ⚠️ Non trovato")
        
        time.sleep(1.5) # Pausa per non essere bannati dal sito

if __name__ == "__main__":
    esegui_aggiornamento()
