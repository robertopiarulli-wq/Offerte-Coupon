import os
import time
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Configurazione Supabase (inserisci i tuoi dati o usa variabili d'ambiente)
URL_SB = "https://fxcuwfpdzymwkemzppgm.supabase.co"
KEY_SB = "sb_publishable__jf5n22-ZlvGPRN-BAh38A_WdVt7B9d" # Usa la Service Role per poter scrivere
sb = create_client(URL_SB, KEY_SB)

def cerca_prodotto_sul_sito(codice, nome):
    search_url = f"https://www.podopiu.com/?s={codice}&post_type=product"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Prova a vedere se la ricerca ha portato direttamente alla pagina prodotto
        # (WooCommerce spesso reindirizza se c'è un match esatto dello SKU)
        product_title = soup.find('h1', class_='product_title')
        if product_title:
            return estrai_dati_pagina(soup)

        # 2. Se è una pagina di risultati, prendi il primo link
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
    # 1. Prendi i prodotti dalla tabella che non hanno ancora l'immagine dello scraper
    prodotti = sb.table("prodotti_catalogo").select("*").is_("IMG_SCRAPER", "null").execute().data
    
    print(f"🚀 Inizio elaborazione di {len(prodotti)} prodotti...")

    for p in prodotti:
        codice_puro = p['CODICE'].split('-')[0] # Prende la parte prima del trattino
        print(f"🔍 Cerco: {codice_puro} ({p['NOME'][:30]}...)")
        
        dati = cerca_prodotto_sul_sito(codice_puro, p['NOME'])
        
        if dati:
            # Aggiorna il prodotto corrente
            sb.table("prodotti_catalogo").update({
                "IMG_SCRAPER": dati['img'],
                "DESCRIZIONE_SCRAPER": dati['desc']
            }).eq("id", p['id']).execute()
            
            # 2. EFFETTO DOMINO: Se fa parte di un gruppo, aggiorna tutti i correlati
            if p['GRUPPO_CORRELATI']:
                sb.table("prodotti_catalogo").update({
                    "IMG_SCRAPER": dati['img'],
                    "DESCRIZIONE_SCRAPER": dati['desc']
                }).eq("GRUPPO_CORRELATI", p['GRUPPO_CORRELATI']).execute()
                print(f" ✅ Gruppo {p['GRUPPO_CORRELATI']} aggiornato!")
            else:
                print(f" ✅ Singolo aggiornato!")
        else:
            print(f" ⚠️ Non trovato sul sito.")
        
        time.sleep(1) # Pausa per non essere bloccati

if __name__ == "__main__":
    esegui_aggiornamento()
