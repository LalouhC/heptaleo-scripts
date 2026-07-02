import urllib.parse
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import email.utils

print("🌍 Initialisation de la veille mondiale Heptaleo (Standardisation des dates) ...")

# 1. Configuration du flux RSS de sortie
fg = FeedGenerator()
fg.id('https://heptaleo.fr')
fg.title('Veille Mondiale Heptathlon & Pentathlon')
fg.description('Flux international automatisé (FR/EN/ES) pour Heptaleo.')
fg.link(href='https://heptaleo.fr', rel='alternate')

# 2. Liste des mots-clés par langue
recherches = [
    {
        "query": "heptathlon OR pentathlon OR 'épreuves combinées' OR 'Léonie Cambours' OR 'Heptaleo' -moderne -décathlon", 
        "lang": "fr", "ce": "FR", "code_lang": "FR"
    },
    {
        "query": "heptathlon OR pentathlon OR 'combined events' OR 'Léonie Cambours' OR 'Heptaleo' -modern -decathlon", 
        "lang": "en", "ce": "US", "code_lang": "EN"
    },
    {
        "query": "heptatlón OR pentatlón OR 'pruebas combinadas' OR 'Léonie Cambours' OR 'Heptaleo' -moderno -decatlón", 
        "lang": "es", "ce": "ES", "code_lang": "ES"
    }
]

urls_ajoutees = set()
tous_les_articles = []

# Date limite réelle : Il y a 30 jours
limite_retroactive = datetime.now(timezone.utc) - timedelta(days=30)

# 3. Récupération des articles depuis Google News
for r in recherches:
    print(f" -> Récupération des articles en [{r['code_lang']}]...")
    
    query_encodee = urllib.parse.quote(r['query'])
    url_google = f"https://news.google.com/rss/search?q={query_encodee}&hl={r['lang']}&gl={r['ce']}&ceid={r['ce']}:{r['lang']}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        reponse = requests.get(url_google, headers=headers)
        soup = BeautifulSoup(reponse.text, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            titre = item.title.text
            lien = item.link.text
            date_brute = item.pubDate.text
            
            try:
                date_parsed = email.utils.parsedate_to_datetime(date_brute)
                date_parsed = date_parsed.astimezone(timezone.utc)
            except Exception:
                date_parsed = datetime.now(timezone.utc)
                
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
        print(f"⚠️ Erreur lors de la récupération [{r['code_lang']}] : {e}")

# --- 4. FILTRAGE ET LIMITES (15 max par langue) ---
articles_recents = [a for a in tous_les_articles if a['date_objet'] >= limite_retroactive]

articles_fr = [a for a in articles_recents if a['langue'] == 'FR']
articles_en = [a for a in articles_recents if a['langue'] == 'EN']
articles_es = [a for a in articles_recents if a['langue'] == 'ES']

# Tri Chronologique RÉEL au sein de chaque langue
articles_fr.sort(key=lambda x: x['date_objet'], reverse=True)
articles_en.sort(key=lambda x: x['date_objet'], reverse=True)
articles_es.sort(key=lambda x: x['date_objet'], reverse=True)

top_fr = articles_fr[:15]
top_en = articles_en[:15]
top_es = articles_es[:15]

# --- 5. ATTRIBUTION DES DATES FICTIVES FORMATÉES POUR START.ME ---
maintenant = datetime.now(timezone.utc)

# Les FR auront la date de maintenant (ex: Aujourd'hui)
for i, art in enumerate(top_fr):
    dt = maintenant - timedelta(minutes=i)
    art['date_rss'] = email.utils.format_datetime(dt)

# Les EN auront la date d'hier (-1 jour)
for i, art in enumerate(top_en):
    dt = maintenant - timedelta(days=1, minutes=i)
    art['date_rss'] = email.utils.format_datetime(dt)

# Les ES auront la date d'avant-hier (-2 jours)
for i, art in enumerate(top_es):
    dt = maintenant - timedelta(days=2, minutes=i)
    art['date_rss'] = email.utils.format_datetime(dt)

# Fusion finale
liste_ordonnee_finale = top_fr + top_en + top_es

# --- 6. GÉNÉRATION DU FLUX XML ---
for art in liste_ordonnee_finale:
    fe = fg.add_entry()
    fe.id(art['lien'])
    fe.title(f"[{art['langue']}] {art['titre']}")
    fe.link(href=art['lien'])
    
    # ASTUCE PROPRE : On force le pubDate avec le format texte standardisé
    fe.pubDate(art['date_rss'])
    
    fe.description(f"Publié le : {art['date_texte']} - Source : Google News ({art['langue']})")

if len(liste_ordonnee_finale) > 0:
    fg.rss_file('flux.xml', pretty=True)
    print(f"✨ Succès ! {len(liste_ordonnee_finale)} articles injectés avec des dates standardisées !")
else:
    print("❌ Aucun article trouvé.")