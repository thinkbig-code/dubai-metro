"""Build the ten language pages of dubaimetro.fyi from src/dubai-metro.html.

Usage (from the repository root):  python3 tools/build.py
Writes index.html, hi.html, ar.html, ur.html, ru.html, de.html, zh.html, fr.html,
sitemap.xml and robots.txt into the repository root. Texts for each language page
(titles, descriptions, the "About this map" section) live in tools/seo_texts.py.
"""
import re, json, html, datetime, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0, HERE)
from seo_texts import TX, ORDER
import seo_pages  # English guide pages: stations, lines, destinations, routes (data from tools/seo_data.json)
SITE=os.environ.get('SITE','https://dubaimetro.fyi/')
OUT=os.environ.get('OUT',ROOT+'/')
s=open(os.path.join(ROOT,'src','dubai-metro.html')).read()
# shared links point to wherever the page is hosted
s,n=re.subn(r'const BASE_URL="[^"]*";','// On your own site, shared links point to wherever this page is hosted\nconst BASE_URL=location.origin+location.pathname;',s)
assert n==1, "BASE_URL line not found"
te=s.index('</title>')+len('</title>');rest=s[te:]
i_map=rest.index('<div id="map"')

# ---------- data from the app, so the text always matches the map ----------
rawblk=s[s.index('const RAW = {'):s.index('};',s.index('const RAW = {'))]
names={m.group(1):m.group(2) for m in re.finditer(r'\b(\w+):\["([^"]+)",-?\d+,-?\d+,',rawblk)}
def arr(n):
    m=re.search(r'const %s=\[([^\]]*)\];'%n,s);return re.findall(r'"(\w+)"',m.group(1))
R_MAIN,R_BR,G,T,M=arr('R_MAIN'),arr('R_BR'),arr('G'),arr('T'),arr('M')
N=lambda i:html.escape(names[i])
lst=lambda ids:', '.join(N(i) for i in ids)
fm=re.search(r'const FARES=\{silver:\[([^\]]*)\],gold:\[([^\]]*)\],red:\[([^\]]*)\]\};',s)
sv,gd,rd=[[x.strip() for x in fm.group(k).split(',')] for k in (1,2,3)]
FV=dict(s0=sv[0],s1=sv[1],s2=sv[2],g0=gd[0],g2=gd[2],r0=rd[0],r2=rd[2])
mono_suspended='mono:"suspended"' in s
TRIPS=[("p_dxb_airport_terminal_3","p_dubai_mall"),("p_dxb_airport_terminal_1","p_dubai_marina_walk"),("p_dxb_airport_terminal_3","p_jbr_the_walk"),
       ("p_dubai_mall","p_atlantis_the_palm"),("p_dubai_mall","p_gold_souk"),("p_al_fahidi_historical_district","p_museum_of_the_future"),
       ("p_dubai_marina_walk","p_mall_of_the_emirates"),("p_dubai_mall","p_expo_city_dubai")]
url=lambda L:SITE+("" if TX[L]["file"]=="index.html" else TX[L]["file"])
fav="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 31s11-10.2 11-18A11 11 0 0 0 5 13c0 7.8 11 18 11 18z' fill='%23E1251B'/%3E%3Crect x='10.5' y='6.5' width='11' height='12' rx='3' fill='%23fff'/%3E%3Crect x='12.3' y='8.6' width='7.4' height='4' rx='1' fill='%23E1251B'/%3E%3Ccircle cx='13.3' cy='15.6' r='1.1' fill='%23E1251B'/%3E%3Ccircle cx='18.7' cy='15.6' r='1.1' fill='%23E1251B'/%3E%3C/svg%3E"
alts='\n'.join(f'<link rel="alternate" hreflang="{L}" href="{url(L)}">' for L in ORDER)+f'\n<link rel="alternate" hreflang="x-default" href="{SITE}">'

# offline support: register the service worker on the public site (https) or a local test server
SW_REG="""
<script>
if("serviceWorker" in navigator&&(location.protocol==="https:"||location.hostname==="localhost")){
  addEventListener("load",()=>{navigator.serviceWorker.register("sw.js").then(()=>navigator.serviceWorker.ready)
    .then(r=>{if(r.active)r.active.postMessage({type:"cache",url:location.pathname});}).catch(()=>{});});
}
</script>"""

# English guide pages, built first so the language pages can link to them
GUIDES=seo_pages.build()
GUIDES_H={"en":"Guides to stations and places","ru":"Путеводитель по станциям и местам (на английском)","hi":"स्टेशनों और जगहों की गाइड (अंग्रेज़ी में)",
  "ar":"أدلة المحطات والأماكن (بالإنجليزية)","ur":"اسٹیشنوں اور جگہوں کی گائیڈ (انگریزی میں)","de":"Stationen und Orte (auf Englisch)",
  "zh":"车站与地点指南（英文）","fr":"Guides des stations et des lieux (en anglais)",
  "tl":"Gabay sa mga istasyon at lugar (sa English)","bn":"স্টেশন ও জায়গার গাইড (ইংরেজিতে)"}
def short(title):
    return title.split(':')[0].replace(' by Metro','')
GUIDE_LINKS=' · '.join(f'<a href="{p}" hreflang="en" lang="en">{html.escape(short(t))}</a>' for p,t in GUIDES.items())

def page(L):
    X=TX[L]
    trips='\n'.join(f'<li><a href="#{a}~{b}~{L}">{html.escape(t)}</a></li>' for (a,b),t in zip(TRIPS,X["trips"]))
    faq='\n'.join(f'<h3>{html.escape(q)}</h3>\n<p>{html.escape(a.format(**FV))}</p>' for q,a in X["q"])
    other=' · '.join(f'<a href="{TX[o]["file"] if TX[o]["file"]!="index.html" else "./"}" hreflang="{o}" lang="{o}">{TX[o]["langName"]}</a>' for o in ORDER if o!=L)
    about=f'''<section id="about" aria-labelledby="aboutH" lang="{L}" dir="{X["dir"]}">
<button id="aboutClose" aria-label="{html.escape(X["close"])}">×</button>
<h1 id="aboutH">{html.escape(X["h1"])}</h1>
<p>{html.escape(X["intro"])}</p>
<p><a href="map/" hreflang="en"><img src="dubai-metro-map.png" width="{seo_pages.MAP_W}" height="{seo_pages.MAP_H}" alt="{html.escape(seo_pages.MAP_ALT)}" loading="lazy" style="width:100%;height:auto;border-radius:12px"></a></p>
<h2>{html.escape(X["popular"])}</h2>
<ul>
{trips}
</ul>
<h2>{html.escape(X["lines"])}</h2>
<p>{X["red"].format(a=N(R_MAIN[0]),b=N(R_MAIN[-1]),c=N(R_BR[0]),d=N(R_BR[-1]))}</p>
<p class="lst" dir="ltr">{lst(R_MAIN)}. {html.escape(X["branch"])}: {lst(R_BR[1:])}.</p>
<p>{X["green"].format(a=N(G[0]),b=N(G[-1]))}</p>
<p class="lst" dir="ltr">{lst(G)}.</p>
<p>{X["tram"]}</p>
<p class="lst" dir="ltr">{lst(T)}.</p>
<p>{X["mono"].format(a=N(M[0]),b=N(M[-1]))}{X["susp"] if mono_suspended else ""}</p>
<p class="lst" dir="ltr">{lst(M)}.</p>
<h2>{html.escape(GUIDES_H[L])}</h2>
<p class="lst" dir="ltr">{GUIDE_LINKS}</p>
<h2>{html.escape(X["faq"])}</h2>
{faq}
<p><a href="https://github.com/thinkbig-code/dubai-metro/issues">{html.escape(X["report"])}</a></p>
<p class="lst">{other}</p>
</section>
'''
    ld={"@context":"https://schema.org","@type":"WebApplication","name":html.unescape(X["ogTitle"]),"url":url(L),
        "description":html.unescape(X["desc"]),"applicationCategory":"TravelApplication","operatingSystem":"Any","isAccessibleForFree":True,
        "inLanguage":L,"offers":{"@type":"Offer","price":"0","priceCurrency":"AED"},
        "about":{"@type":"Place","name":"Dubai","address":{"@type":"PostalAddress","addressCountry":"AE"}}}
    oglocs='\n'.join(f'<meta property="og:locale:alternate" content="{TX[o]["locale"]}">' for o in ORDER if o!=L)
    head=f'''<!doctype html>
<html lang="{L}" data-pagelang="{L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{X["title"]}</title>
<meta name="description" content="{X["desc"]}">
<link rel="canonical" href="{url(L)}">
{alts}
<meta name="robots" content="index,follow">
<meta name="msvalidate.01" content="26F6B07BDF6CE6FA1D82E4B9966FBEFF">
<meta property="og:type" content="website">
<meta property="og:url" content="{url(L)}">
<meta property="og:locale" content="{X["locale"]}">
{oglocs}
<meta property="og:title" content="{X["ogTitle"]}">
<meta property="og:description" content="{X["ogDesc"]}">
<meta property="og:image" content="{SITE}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F4F7F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10161C" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{fav}">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False)}</script>
<!-- anonymous visit counter (GoatCounter): no cookies, no personal data -->
<script data-goatcounter="https://dubaimetro.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<style>body{{margin:0}}[hidden]{{display:none!important}}img{{max-width:100%}}</style>
'''
    # the English root page keeps the visitor's own language; the others open in theirs
    if L=="en": head=head.replace(' data-pagelang="en"','')
    return head+rest[:i_map]+'</head>\n<body>\n'+about+rest[i_map:]+SW_REG+'\n</body>\n</html>\n'

for L in ORDER:
    open(OUT+TX[L]["file"],'w').write(page(L))
import hashlib
ver=hashlib.sha1(''.join(open(OUT+TX[L]["file"]).read() for L in ORDER).encode()).hexdigest()[:10]
manifest={"name":"Dubai Metro Map & Route Planner","short_name":"Dubai Metro","description":html.unescape(TX["en"]["ogDesc"]),
  "start_url":"./","scope":"./","display":"standalone","background_color":"#F4F7F8","theme_color":"#F4F7F8",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}
open(OUT+'manifest.webmanifest','w').write(json.dumps(manifest,ensure_ascii=False,indent=1))
open(OUT+'sw.js','w').write(open(os.path.join(HERE,'sw.template.js')).read().replace('__VERSION__',ver))
today=datetime.date.today().isoformat()
xl='\n'.join(f'    <xhtml:link rel="alternate" hreflang="{o}" href="{url(o)}"/>' for o in ORDER)+f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}"/>'
urls='\n'.join(f'  <url>\n    <loc>{url(L)}</loc>\n    <lastmod>{today}</lastmod>\n{xl}\n  </url>' for L in ORDER)
IMG=f'\n    <image:image><image:loc>{SITE}{seo_pages.MAP_IMG}</image:loc></image:image>'
urls='\n'.join(f'  <url>\n    <loc>{url(L)}</loc>\n    <lastmod>{today}</lastmod>\n{xl}{IMG}\n  </url>' for L in ORDER)
urls+='\n'+'\n'.join(f'  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{today}</lastmod>{IMG if p in ("map/","stations/") else ""}\n  </url>' for p in GUIDES)
open(OUT+'sitemap.xml','w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n{urls}\n</urlset>\n')
open(OUT+'robots.txt','w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
print("deploy built:",', '.join(TX[L]["file"] for L in ORDER),"+",len(GUIDES),"guide pages")
