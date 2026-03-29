import os
import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# MODIFICA QUI: Legge le credenziali dalle variabili d'ambiente di GitHub
URL_SB = os.environ.get("https://fxcuwfpdzymwkemzppgm.supabase.co")
KEY_SB = os.environ.get("sb_publishable__jf5n22-ZlvGPRN-BAh38A_WdVt7B9d")

if not URL_SB or not KEY_SB:
    print("❌ Errore: Credenziali Supabase non trovate nelle variabili d'ambiente.")
    exit(1)

sb = create_client(URL_SB, KEY_SB)

def cerca_prodotto_sul_sito(codice, nome):
    # (Il resto della funzione rimane uguale...)
    search_url = f"https://www.podopiu.com/?s={codice}&post_type=product"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        product_title = soup.find('h1', class_='product_title')
        if product_title:
            return estrai_dati_pagina(soup)
        primo_prodotto = soup.select_one('ul.products li.product a')
        if primo_prodotto:
            link = primo_prodotto['href']
            res_p = requests.get(link, headers=headers)
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
    # Prende solo i prodotti dove IMG_SCRAPER è ancora vuoto (NULL)
    # Nota: su Supabase 'is_null' si usa così:
    prodotti = sb.table("prodotti_catalogo").select("*").is_("IMG_SCRAPER", "null").execute().data
    
    print(f"🚀 Inizio elaborazione di {len(prodotti)} prodotti...")

    for p in prodotti:
        # Pulizia codice: prende solo la parte prima del trattino
        codice_puro = p['CODICE'].split('-')[0] if p['CODICE'] else ""
        if not codice_puro: continue

        print(f"🔍 Cerco: {codice_puro} ({p['NOME'][:30]}...)")
        dati = cerca_prodotto_sul_sito(codice_puro, p['NOME'])
        
        if dati:
            # Aggiorna il prodotto corrente
            sb.table("prodotti_catalogo").update({
                "IMG_SCRAPER": dati['img'],
                "DESCRIZIONE_SCRAPER": dati['desc']
            }).eq("id", p['id']).execute()
            
            # EFFETTO DOMINO: Aggiorna tutti i prodotti con lo stesso gruppo
            if p['GRUPPO_CORRELATI'] and p['GRUPPO_CORRELATI'] != "":
                sb.table("prodotti_catalogo").update({
                    "IMG_SCRAPER": dati['img'],
                    "DESCRIZIONE_SCRAPER": dati['desc']
                }).eq("GRUPPO_CORRELATI", p['GRUPPO_CORRELATI']).execute()
                print(f" ✅ Gruppo {p['GRUPPO_CORRELATI']} aggiornato!")
            else:
                print(f" ✅ Singolo aggiornato!")
        else:
            print(f" ⚠️ Non trovato sul sito.")
        
        time.sleep(1)

if __name__ == "__main__":
    esegui_aggiornamento()
