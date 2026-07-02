import urllib.parse
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import email.utils

print("🌍 Initialisation de la veille mondiale Heptaleo (Requêtes Séparées) ...")

# 1. Configuration du flux RSS de sortie
fg = FeedGenerator()
fg.id('https://heptaleo.fr')
fg.title('Veille Mondiale Heptathlon & Pentathlon')
fg.description('Flux international automatisé (FR/EN/ES) pour Heptaleo.')
fg.link(href='https://heptaleo.fr', rel='alternate')

# 2. Séparation des requêtes pour éviter que Léonie ne masque le reste
requetes_sources = [
    # Français
    {"query": "heptathlon OR pentathlon OR 'épreuves combinées'", "lang": "fr", "ce": "FR", "code_lang": "FR"},
    {"query": "'Léonie Cambours' OR 'Heptaleo'", "lang": "fr", "ce": "FR", "code_lang": "FR"},
    
    # Anglais
    {"query": "heptathlon OR pentathlon OR 'combined events'", "lang": "en", "ce": "US", "code_lang": "EN"},
    {"query": "'Léonie Cambours' OR 'Heptaleo'", "lang": "en", "ce": "US", "code_lang": "EN"},
    
    # Espagnol
    {"query": "heptatlón OR pentatlón OR 'pruebas combinadas'", "lang": "es", "ce": "ES", "code_lang": "ES"},
    {"query": "'Léonie Cambours' OR 'Heptaleo'", "lang": "es", "ce": "ES", "code_lang": "ES"}
]

urls_ajoutees = set()
tous_les_articles = []

# 3. Récupération auprès de Google News
for r in requetes_sources:
    query_encodee = urllib.parse.quote(r['query'])
    url_google = f"https://news.google.com/rss/search?q={query_encodee}&hl={r['lang']}&gl={r['ce']}&ceid={r['ce']}:{r['lang']}"
    
    try:
        reponse = requests.get(url_google, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(reponse.text, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            titre = item.title.text
            lien = item.link.text
            date_brute = item.pubDate.text
            
            try:
                date_parsed = email.utils.parsedate_to_datetime(date_brute).astimezone(timezone.utc)
            except Exception:
                date_parsed = datetime.now(timezone.utc)
                
            # Élimination des vrais doublons de liens
            if lien not in urls_ajoutees:
                urls_ajoutees.add(lien)
                tous_les_articles.append({
                    "titre": titre,
                    "lien": lien,
                    "date_texte": date_brute,
                    "date_objet": date_parsed,
                    "langue": r['code_lang']
                })
    except Exception as e:
        print(f"⚠️ Erreur de liaison Google News : {e}")

# --- 4. TRIS CHRONOLOGIQUE PUR (Sans distinction de langue) ---
# On trie TOUT du plus récent au plus ancien, point barre.
tous_les_articles.sort(key=lambda x: x['date_objet'], reverse=True)

# Limite globale pour ne pas surcharger (par exemple les 40 derniers articles mondiaux)
articles_finaux = tous_les_articles[:40]

# --- 5. GÉNÉRATION DU FLUX RSS ---
for art in articles_finaux:
    fe = fg.add_entry()
    fe.id(art['lien'])
    fe.title(f"[{art['langue']}] {art['titre']}")
    fe.link(href=art['lien'])
    fe.pubDate(email.utils.format_datetime(art['date_objet']))
    fe.description(f"Publié le : {art['date_texte']} - Source : Google News ({art['langue']})")

if len(articles_finaux) > 0:
    fg.rss_file('flux.xml', pretty=True)
    print(f"✨ Succès ! {len(articles_finaux)} articles mondiaux mélangés et triés par date.")
else:
    print("❌ Aucun article trouvé.")