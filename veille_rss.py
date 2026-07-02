import urllib.parse
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup

print("🌍 Initialisation de la veille mondiale Heptaleo ...")

# 1. Configuration du flux RSS de sortie
fg = FeedGenerator()
fg.id('https://heptaleo.fr')
fg.title('Veille Mondiale Heptathlon & Pentathlon')
fg.description('Flux international automatisé (FR/EN/ES) pour Heptaleo.')
fg.link(href='https://heptaleo.fr', rel='alternate')

# 2. Liste des mots-clés par langue
recherches = [
    # Français : On cherche les combinées, mais on exclut le pentathlon moderne et le décathlon
    {"query": "heptathlon OR pentathlon OR 'épreuves combinées' -moderne -décathlon", "lang": "fr", "ce": "FR"},
    
    # Anglais : On exclut "modern" (pentathlon) et "decathlon"
    {"query": "heptathlon OR pentathlon OR 'combined events' -modern -decathlon", "lang": "en", "ce": "US"},
    
    # Espagnol : On exclut "moderno" et "decatlón"
    {"query": "heptatlón OR pentatlón OR 'pruebas combinadas' -moderno -decatlón", "lang": "es", "ce": "ES"}
]

urls_ajoutees = set()  # Pour éviter les doublons si un article sort dans plusieurs langues
articles_trouves = 0

# 3. Boucle sur chaque langue
for r in recherches:
    print(f" -> Recherche des articles en [{r['lang'].upper()}]...")
    
    # On encode la recherche pour que Google la comprenne (ex: les espaces deviennent %20)
    query_encodée = urllib.parse.quote(r['query'])
    
    # URL du flux RSS de Google News avec filtres
    url_google = f"https://news.google.com/rss/search?q={query_encodée}&hl={r['lang']}&gl={r['ce']}&ceid={r['ce']}:{r['lang']}"
    
    # On va lire le flux de Google
    headers = {"User-Agent": "Mozilla/5.0"}
    reponse = requests.get(url_google, headers=headers)
    soup = BeautifulSoup(reponse.text, 'xml') # On utilise le lecteur XML
    
   
    items = soup.find_all('item')[:10]
    
    for item in items:
        titre = item.title.text
        lien = item.link.text
        date = item.pubDate.text
        
        # Si on n'a pas déjà ajouté cet article
        if lien not in urls_ajoutees:
            urls_ajoutees.add(lien)
            
            # On l'ajoute à ton flux RSS Heptaleo
            fe = fg.add_entry()
            fe.id(lien)
            fe.title(f"[{r['lang'].upper()}] {titre}")
            fe.link(href=lien)
            fe.description(f"Publié le : {date} - Source : Google News ({r['lang'].upper()})")
            
            articles_trouves += 1

# 4. Sauvegarde finale
if articles_trouves > 0:
    fg.rss_file('flux.xml', pretty=True)
    print(f"✨ Succès ! {articles_trouves} articles internationaux filtrés et centralisés dans flux.xml ! 🔥")
else:
    print("❌ Aucun article trouvé aujourd'hui avec ces critères.")