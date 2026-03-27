def esegui_scraping():
    home_url = "https://share.google/2a1HjpodGQ2SYBLZe" 
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(home_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Cerchiamo tutti i link che hanno la parola 'category' nella classe o nell'URL
    categorie_links = [a for a in soup.find_all('a') if 'category' in str(a.get('class')) or 'category' in a.get('href', '')] 
    
    for cat in categorie_links:
        nome_categoria = cat.text.strip()
        link_categoria = cat['href']
        
        # Gestione link relativi
        if not link_categoria.startswith('http'):
            link_categoria = "https://tuo-sito-base.com" + link_categoria

        res_cat = requests.get(link_categoria, headers=headers)
        soup_cat = BeautifulSoup(res_cat.text, 'html.parser')
        
        # Cerchiamo i box prodotto usando i tag che hai visto (es. quelli con 'product')
        items = soup_cat.find_all('div', class_=lambda x: x and 'product' in x)
        
        for item in items:
            try:
                # Prendiamo il primo H3 o H4 che troviamo (di solito è il titolo)
                titolo = item.find(['h2', 'h3', 'h4'])
                # Prendiamo la prima immagine che ha 'zoom' o 'product' o la prima in assoluto
                img = item.find('img', class_=lambda x: x and ('zoom' in x or 'product' in x)) or item.find('img')
                
                p_data = {
                    "codice": "SC-" + titolo.text.strip()[:5].upper() if titolo else "N/D", 
                    "nome": titolo.text.strip() if titolo else "Prodotto senza nome",
                    "immagine_url": img['src'] if img else "",
                    "descrizione": item.text.strip()[:100], # Prende i primi 100 caratteri del box come descrizione
                    "categoria": nome_categoria 
                }
                
                supabase.table("prodotti").upsert(p_data, on_conflict="nome").execute()
            except:
                continue
