import urllib.parse
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import email.utils

print("🌍 Initialisation de la veille mondiale Heptaleo (Sans aucun filtre restrictif) ...")

# 1. Configuration du flux RSS de sortie
fg = FeedGenerator()
fg.id('https://heptaleo.fr')
fg.title('Veille Mondiale Heptathlon & Pentathlon')
fg.description('Flux international automatisé (FR/EN/ES) pour Heptaleo.')
fg.link(href='https://heptaleo.fr', rel='alternate')

# 2. Requêtes directes (Google gère le tri de base)
recherches = [
    {"query": "heptathlon OR pentathlon OR 'épreuves combinées' OR 'Léonie Cambours' OR 'Heptaleo'", "lang": "fr", "ce": "FR", "code_lang": "FR"},
    {"query": "heptathlon OR pentathlon OR 'combined events' OR 'Léonie Cambours' OR 'Heptaleo'", "lang": "en", "ce": "US", "code_lang": "EN"},
    {"query": "heptatlón OR pentatlón OR 'pruebas combinadas' OR 'Léonie Cambours' OR 'Heptaleo'", "lang": "es", "ce": "ES", "code_lang": "ES"}
]

urls_ajoutees = set()
tous_les_articles = []

# Date limite large (30 jours)
limite_retroactive = datetime.now(timezone.utc) - timedelta(days=30)

# 3. Récupération directe depuis Google News
for r in recherches:
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
                
            if date_parsed >= limite_retroactive and lien not in urls_ajoutees:
                urls_ajoutees.add(lien)
                tous_les_articles.append({
                    "titre": titre,
                    "lien": lien,
                    "date_texte": date_brute,
                    "date_objet": date_parsed,
                    "langue": r['code_lang']
                })
    except Exception as e:
        print(f"⚠️ Erreur [{r['code_lang']}] : {e}")

# --- 4. TRIS ET RÉPARTITION PAR LANGUE ---
articles_fr = [a for a in tous_les_articles if a['langue'] == 'FR']
articles_en = [a for a in tous_les_articles if a['langue'] == 'EN']
articles_es = [a for a in tous_les_articles if a['langue'] == 'ES']

articles_fr.sort(key=lambda x: x['date_objet'], reverse=True)
articles_en.sort(key=lambda x: x['date_objet'], reverse=True)
articles_es.sort(key=lambda x: x['date_objet'], reverse=True)

# On prend les 15 meilleurs de chaque langue
liste_ordonnee_finale = articles_fr[:15] + articles_en[:15] + articles_es[:15]
maintenant = datetime.now(timezone.utc)

# --- 5. GÉNÉRATION DU XML AVEC DATES STRATÉGIQUES POUR START.ME ---
for i, art in enumerate(liste_ordonnee_finale):
    fe = fg.add_entry()
    fe.id(art['lien'])
    fe.title(f"[{art['langue']}] {art['titre']}")
    fe.link(href=art['lien'])
    
    # Gestion de la date artificielle pour forcer l'ordre des blocs sur Start.me
    if art['langue'] == 'FR':
        dt = maintenant - timedelta(minutes=i)
    elif art['langue'] == 'EN':
        dt = maintenant - timedelta(days=1, minutes=i)
    else:
        dt = maintenant - timedelta(days=2, minutes=i)
        
    fe.pubDate(email.utils.format_datetime(dt))
    fe.description(f"Publié le : {art['date_texte']} - Source : Google News ({art['langue']})")

# --- 6. SÉCURITÉ DE VÉRIFICATION ET ÉCRITURE ---
if len(liste_ordonnee_finale) > 0:
    fg.rss_file('flux.xml', pretty=True)
    print(f"✨ Succès ! {len(liste_ordonnee_finale)} articles injectés sans aucun filtre bloquant.")
else:
    print("❌ Aucun article trouvé.")