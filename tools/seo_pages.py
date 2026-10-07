"""Build the English guide pages (stations, lines, destinations, routes) of dubaimetro.fyi.

Usage (from the repository root, after tools/export_data.js):  python3 tools/seo_pages.py
Called by tools/build.py. Reads tools/seo_config.json (which pages exist) and tools/seo_data.json
(the app's own data and routes it calculated). No fact on these pages is typed by hand: names,
lines, zones, walk times, travel times and fares all come from the app, so a data fix reaches
every page on the next export and build.
Returns the list of page paths, for the sitemap.
"""
import json, html, os, math, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SITE = os.environ.get('SITE', 'https://dubaimetro.fyi/')
OUT = os.environ.get('OUT', ROOT + '/')
CFG = json.load(open(os.path.join(HERE, 'seo_config.json')))
D = json.load(open(os.path.join(HERE, 'seo_data.json')))
ST, EN, ZONE, FARES = D['stations'], D['en'], D['zone'], D['fares']
SVC = {s['id']: s for s in D['services']}
PL = {p['id']: p for p in D['places']}
WALKS = D['walks']
SUSP = {k for k, v in D['status'].items() if v == 'suspended'}
LINE_KIND = {'red': 'metro', 'green': 'metro', 'tram': 'tram', 'mono': 'mono'}
LINE_NAME = {'red': EN['lgRed'], 'green': EN['lgGreen'], 'tram': EN['lgTram'], 'mono': EN['lgMono']}
LINE_COLOR = {'red': '#E1251B', 'green': '#4CB848', 'tram': '#F7931E', 'mono': '#3D7DCA'}
LINE_PAGE = {'red': 'lines/red-line/', 'green': 'lines/green-line/', 'tram': 'tram/', 'mono': 'palm-monorail/'}
e = html.escape


def t(key, **kw):
    s = EN[key]
    if isinstance(s, dict):
        s = s['one'] if kw.get('n') == 1 else s['other']
    for k, v in kw.items():
        s = s.replace('{' + k + '}', str(v))
    return s


# ---------------- what exists ----------------
PAGES = {}            # path -> title, for links and the sitemap
STATION_PAGE = {}     # station id -> path of a page about it
for s in CFG['stations']:
    STATION_PAGE[s['id']] = 'stations/%s/' % s['slug']
DEST_PAGE = {}        # place id -> path
for d in CFG['destinations']:
    for pid in [d['main']] + d['also']:
        DEST_PAGE.setdefault(pid, 'destinations/%s/' % d['slug'])
PAIR_PAGE = {}        # "a~b" -> route page path
for r in CFG['routes']:
    for a, b in r['pairs']:
        PAIR_PAGE[a + '~' + b] = 'routes/%s/' % r['slug']
    PAIR_PAGE['~'.join(r['return'])] = 'routes/%s/' % r['slug']


def station_links(sid):
    """pages about a station: its own page and destination pages whose place uses it"""
    out = []
    if sid in STATION_PAGE:
        out.append((STATION_PAGE[sid], ST[sid]['n'] + ' station'))
    for d in CFG['destinations']:
        if PL[d['main']]['st'] == sid:
            out.append(('destinations/%s/' % d['slug'], d['title']))
    return out


def other_names(sid):
    n = ST[sid]['n'].lower()
    return [x for x in ST[sid]['f'] if x.lower() not in n]


# ---------------- route facts ----------------
def end_of(tok):
    if tok in ST:
        return {'st': tok, 'name': ST[tok]['n'], 'lm': None}
    p = PL[tok]
    return {'st': p['st'], 'name': p['n'], 'lm': p}


def direction(leg):
    s = SVC[leg['svc']]; stops = s['stops']
    i0, i1 = stops.index(leg['stops'][0]), stops.index(leg['stops'][-1])
    fwd = i1 > i0
    if s['line'] == 'red':
        np_i = SVC['R1']['stops'].index('np')
        if not fwd:
            return 'Centrepoint'
        if i1 > np_i:
            return 'Life Pharmacy' if leg['svc'] == 'R1' else 'Expo 2020'
        return t('or', a='Life Pharmacy', b='Expo 2020')
    if s['line'] == 'green':
        return 'Creek' if fwd else 'e&'
    if s['line'] == 'tram':
        return 'Al Sufouh' if leg['svc'] == 'T' else 'JBR 1'
    return 'Atlantis Aquaventure' if fwd else 'Palm Gateway'


def mono_fare(a, b):
    return D['monoFares'].get(a + '|' + b) or D['monoFares'].get(b + '|' + a)


def fare(v):
    zs, mono = set(), 0
    for l in v['legs']:
        if l['type'] != 'ride':
            continue
        if l['line'] == 'mono':
            mono += mono_fare(l['stops'][0], l['stops'][-1]) or 0
        else:
            zs.update(ZONE[x] for x in l['stops'])
    if not zs:
        return {'zones': 0, 'silver': None, 'gold': None, 'red': None, 'mono': mono}
    i = min(len(zs), 3) - 1
    return {'zones': len(zs), 'silver': FARES['silver'][i], 'gold': FARES['gold'][i], 'red': FARES['red'][i], 'mono': mono}


def aed(x):
    return ('%g' % x)


def fare_text(f):
    if f['silver'] is None and not f['mono']:
        return 'no fare (on foot)'
    if f['silver'] is None:
        return 'AED %s (Palm Monorail ticket)' % aed(f['mono'])
    s = 'AED %s' % aed(f['silver'])
    if f['mono']:
        s += ' + AED %s monorail' % aed(f['mono'])
    return s


def lines_of(v):
    out = []
    for l in v['legs']:
        if l['type'] == 'ride':
            out.append(l['line'])
        elif l['type'] == 'walk':
            out.append('walk')
    return out


def chips(v):
    h = []
    for x in lines_of(v):
        if x == 'walk':
            h.append('<span class="chip w">walk</span>')
        else:
            h.append('<span class="chip" style="--c:%s">%s</span>' % (LINE_COLOR[x], e(LINE_NAME[x])))
    return ' '.join(h)


def suspended_in(v):
    return any(l['type'] == 'ride' and LINE_KIND[l['line']] in SUSP for l in v['legs'])


def steps(v, a, b):
    A, B = end_of(a), end_of(b)
    legs = list(v['legs'])
    lead = legs.pop(0) if legs and legs[0]['type'] == 'walk' else None
    tail = legs.pop() if legs and legs[-1]['type'] == 'walk' else None
    out = []
    if A['lm']:
        lm = A['lm']
        if lead:
            out.append((t('goTo', s=ST[lead['to']]['n']), t('onFootFrom', n=lead['t'] + (lm.get('min') or 0), x=lm['n'])))
        else:
            sub = t(lm['note']) if lm.get('note') else t('fromPlace', n=lm['min'], p=lm['n'], w=t(lm['walk'])) if lm.get('min') else t('nearestTo', p=lm['n'])
            out.append((t('goTo', s=ST[A['st']]['n']), sub))
    elif lead:
        out.append((t('walkTo', s=ST[lead['to']]['n']), t('onFootFrom', n=lead['t'], x=ST[lead['from']]['n'])))
    for i, l in enumerate(legs):
        if l['type'] == 'ride':
            n = len(l['stops']) - 1
            first = i == 0 or legs[i - 1]['type'] == 'walk'
            sub = (t('boardAt', s=ST[l['stops'][0]]['n']) + ' · ' if first else '') + t('stops', n=n) + ' · ' + t('min', n=round(l['min']))
            out.append((t('take', l=LINE_NAME[l['line']], d=direction(l)), sub + ' · ' + t('getOff', s=ST[l['stops'][-1]]['n'])))
        elif l['type'] == 'xfer':
            nxt = legs[i + 1]
            same = nxt['line'] == legs[i - 1]['line']
            if same:
                out.append((t('changeTrains', s=ST[l['from']]['n']), t('waitPlatform', d='Expo 2020' if nxt['svc'] == 'R2' else 'Life Pharmacy', n=l['t'])))
            else:
                out.append((t('changeTo', l=LINE_NAME[nxt['line']]), t('followSigns', l=LINE_NAME[nxt['line']], s=ST[l['from']]['n'], n=l['t'])))
        else:
            w = next(w for w in WALKS if {w['a'], w['b']} == {l['from'], l['to']})
            out.append((t('walkTo', s=ST[l['to']]['n']), t('onFootOut' if w.get('long') else 'onFootSign', n=l['t'])))
    if B['lm']:
        lm = B['lm']
        if tail:
            out.append((t('walkToPlace', p=lm['n']), t('onFootFrom', n=tail['t'] + (lm.get('min') or 0), x=ST[tail['from']]['n'])))
        elif lm.get('note'):
            out.append((lm['n'], t(lm['note'])))
        else:
            out.append((t('walkToPlace', p=lm['n']), t('placeWalk', n=lm['min'], w=t(lm['walk'])) if lm.get('min') else t('noWalkData')))
    elif tail:
        out.append((t('walkTo', s=ST[tail['to']]['n']), t('onFootFrom', n=tail['t'], x=ST[tail['from']]['n'])))
    return out


def best(a, b):
    vs = D['routes'][a + '~' + b]
    return next((v for v in vs if 'fast' in v['modes']), vs[0]), vs


def xf_text(n):
    return 'no change' if n == 0 else ('1 change' if n == 1 else '%d changes' % n)


def span(v):
    return ('%d min' % v['time']) if v['time'] == v['timeMax'] else ('%d–%d min' % (v['time'], v['timeMax']))


def summary(v):
    return '%s · %s · %d min walking · %s' % (span(v), xf_text(v['xf']), v['walk'], fare_text(fare(v)))


# ---------------- hours ----------------
DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def hm(m):
    m = m % 1440
    return '%02d:%02d' % (m // 60, m % 60)


def hours_rows(kind):
    H = D['hours'][kind]
    order = [1, 2, 3, 4, 5, 6, 0]  # Monday first
    groups = []
    for d in order:
        o, c = H[d]
        if groups and groups[-1][1] == (o, c):
            groups[-1][0].append(d)
        else:
            groups.append([[d], (o, c)])
    rows = []
    for ds, (o, c) in groups:
        days = DAYS[ds[0]] if len(ds) == 1 else '%s–%s' % (DAYS[ds[0]], DAYS[ds[-1]])
        rows.append((days, hm(o), hm(c) + (' (next day)' if c > 1440 else '')))
    return rows


def hours_html(kinds):
    h = ['<h2 id="hours">Opening hours</h2>']
    for k in kinds:
        label = {'metro': 'Dubai Metro', 'tram': 'Dubai Tram', 'mono': 'Palm Monorail'}[k]
        if k in SUSP:
            h.append('<p><b>%s</b>: %s</p>' % (label, e(t('monoSuspended'))))
            continue
        h.append('<table class="hrs"><caption>%s</caption><tr><th>Days</th><th>First</th><th>Closes</th></tr>' % label)
        h.extend('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % r for r in hours_rows(k))
        h.append('</table>')
    h.append('<p class="note">%s Hours change during Ramadan and on public holidays.</p>' % e(t('hoursNote')))
    return '\n'.join(h)


# ---------------- page frame ----------------
FAV = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 31s11-10.2 11-18A11 11 0 0 0 5 13c0 7.8 11 18 11 18z' fill='%23E1251B'/%3E%3Crect x='10.5' y='6.5' width='11' height='12' rx='3' fill='%23fff'/%3E%3Crect x='12.3' y='8.6' width='7.4' height='4' rx='1' fill='%23E1251B'/%3E%3Ccircle cx='13.3' cy='15.6' r='1.1' fill='%23E1251B'/%3E%3Ccircle cx='18.7' cy='15.6' r='1.1' fill='%23E1251B'/%3E%3C/svg%3E"
CSS = """
:root{--bg:#F4F7F8;--surface:#fff;--fg:#14202B;--muted:#5B6773;--rule:#DCE3E8;--accent:#0B6E99;--warn:#8A4B00;--warnbg:#FFF4E0}
@media (prefers-color-scheme:dark){:root{--bg:#10161C;--surface:#18212A;--fg:#E6EDF2;--muted:#9AA7B2;--rule:#2A3742;--accent:#6CC4EE;--warn:#FFCF8A;--warnbg:#2E2414}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
header.top{background:var(--surface);border-bottom:1px solid var(--rule)}
header.top nav{max-width:860px;margin:0 auto;padding:10px 16px;display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-size:14px}
@media (max-width:420px){header.top nav{gap:10px;font-size:13px}}
header.top .brand{font-weight:700;color:var(--fg);text-decoration:none;margin-inline-end:auto}
main{max-width:860px;margin:0 auto;padding:16px 16px 40px}
.crumbs{font-size:13px;color:var(--muted);margin:4px 0 8px}
.crumbs a{color:var(--muted)}
h1{font-size:28px;line-height:1.2;margin:8px 0 12px}
h2{font-size:20px;margin:28px 0 8px}
h3{font-size:16px;margin:18px 0 6px}
.lead{font-size:18px}
.cta{display:inline-block;background:#E1251B;color:#fff;text-decoration:none;font-weight:600;padding:10px 16px;border-radius:999px;margin:6px 0}
.cta.sm{font-size:14px;padding:6px 12px}
.cta.alt{background:var(--surface);color:var(--accent);border:1px solid var(--rule)}
.mapl{font-size:12px;font-weight:600;text-decoration:none;border:1px solid var(--rule);border-radius:999px;padding:0 6px;margin-inline-start:4px;white-space:nowrap}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:12px 14px;margin:10px 0}
.sum{font-weight:600}
.chip{display:inline-block;font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;background:var(--c);color:#fff}
.chip.w{background:var(--rule);color:var(--fg)}
ol.steps{padding-inline-start:20px;margin:8px 0}
ol.steps li{margin:6px 0}
ol.steps .sub{display:block;color:var(--muted);font-size:14px}
table{border-collapse:collapse;width:100%;margin:8px 0;background:var(--surface);font-size:15px}
th,td{border:1px solid var(--rule);padding:6px 8px;text-align:start;vertical-align:top}
th{background:var(--bg);font-weight:600}
caption{text-align:start;font-weight:600;padding:4px 0}
.scroll{overflow-x:auto}
.warn{background:var(--warnbg);color:var(--warn);border-radius:10px;padding:10px 12px;margin:10px 0}
.note,.muted{color:var(--muted);font-size:14px}
footer{max-width:860px;margin:0 auto;padding:16px;border-top:1px solid var(--rule);color:var(--muted);font-size:13px}
ul.links{padding-inline-start:18px}
@media (max-width:560px){h1{font-size:24px}table{font-size:14px}}
"""


def frame(path, title, desc, body, crumbs, ld_extra=None, og_image='og-image.png'):
    depth = path.count('/')
    root = '../' * depth
    PAGES[path] = title
    url = SITE + path
    crumb_html = ' › '.join(['<a href="%s">Dubai Metro Map</a>' % root] + ['<a href="%s%s">%s</a>' % (root, p, e(n)) for p, n in crumbs[:-1]] + [e(crumbs[-1][1])]) if crumbs else ''
    items = [{"@type": "ListItem", "position": 1, "name": "Dubai Metro Map", "item": SITE}] + \
            [{"@type": "ListItem", "position": i + 2, "name": n, "item": SITE + p} for i, (p, n) in enumerate(crumbs)]
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}]
    if ld_extra:
        ld.append(ld_extra)
    body = body.replace('{ROOT}', root)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F4F7F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10161C" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{FAV}">
<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script data-goatcounter="https://dubaimetro.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<style>{CSS}</style>
</head>
<body>
<header class="top"><nav><a class="brand" href="{root}">Dubai Metro Map</a><a href="{root}lines/red-line/">Red Line</a><a href="{root}lines/green-line/">Green Line</a><a href="{root}tram/">Tram</a><a href="{root}stations/">Stations</a><a href="{root}map/">Map image</a></nav></header>
<main>
<div class="crumbs">{crumb_html}</div>
{body}
</main>
<footer>
<p>{e(t('foot'))} {e(t('attrib'))} Travel times on this page are for a weekday at midday, including typical waiting.</p>
<p>An independent, non-commercial map, not affiliated with RTA. <a href="mailto:callmebackemail@protonmail.com?subject=Dubai%20Metro%20Map">Report a problem</a> · <a href="{root}">Open the interactive map</a></p>
</footer>
</body>
</html>
'''


def write(path, content):
    full = os.path.join(OUT, path, 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w').write(content)


def plan(a, b, label='Open this route on the map', small=False):
    return '<a class="cta%s" href="{ROOT}#%s~%s~en">%s</a>' % (' sm' if small else '', a, b, e(label))


def route_card(a, b, heading=None, show_alt=True):
    v, vs = best(a, b)
    h = ['<div class="card">']
    if heading:
        h.append('<h3>%s</h3>' % e(heading))
    if suspended_in(v):
        h.append('<div class="warn">%s This route uses it, so it cannot be travelled right now.</div>' % e(t('monoSuspended')))
    h.append('<p class="sum">%s</p><p>%s</p>' % (e(summary(v)), chips(v)))
    h.append('<ol class="steps">' + ''.join('<li>%s<span class="sub">%s</span></li>' % (e(a1), e(b1)) for a1, b1 in steps(v, a, b)) + '</ol>')
    # same rule as the app: only the route with fewer changes, and only if it costs at most 5 minutes more
    others = [x for x in vs if x is not v and 'few' in x['modes'] and x['xf'] < v['xf'] and x['time'] - v['time'] <= 5]
    if show_alt and others:
        h.append('<p class="muted">With fewer changes: ' + '; '.join(summary(x) for x in others) + '.</p>')
    h.append(plan(a, b, small=True))
    h.append('</div>')
    return '\n'.join(h)


def routes_table(pairs, label_of):
    rows = ['<div class="scroll"><table><tr><th>From</th><th>To</th><th>Lines</th><th>Time</th><th>Changes</th><th>Fare (Silver Nol)</th><th></th></tr>']
    for a, b in pairs:
        v, _ = best(a, b)
        page = PAIR_PAGE.get(a + '~' + b)
        more = ('<a href="{ROOT}%s">Step by step</a> · ' % page) if page else ''
        warn = ' <span class="muted">(not running now)</span>' if suspended_in(v) else ''
        rows.append('<tr><td>%s</td><td>%s</td><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s<a href="{ROOT}#%s~%s~en">Map</a></td></tr>' % (
            e(end_of(a)['name']), e(end_of(b)['name']), chips(v), warn, span(v), xf_text(v['xf']), e(fare_text(fare(v))), more, a, b))
    rows.append('</table></div>')
    return '\n'.join(rows)


def km(a, b):
    (la1, lo1), (la2, lo2) = D['geo'][a], D['geo'][b]
    return math.hypot(la1 - la2, (lo1 - lo2) * math.cos(math.radians(25.2))) * 111


def station_facts(sid):
    s = ST[sid]
    lines = ', '.join(LINE_NAME[l] for l in s['lines'])
    rows = [('Lines', lines)]
    if other_names(sid):
        rows.append(('Other or former names', ', '.join(other_names(sid))))
    if sid in ZONE and 'mono' not in s['lines']:
        rows.append(('Nol fare zone', str(ZONE[sid])))
    for w in WALKS:
        if sid in (w['a'], w['b']):
            o = w['b'] if w['a'] == sid else w['a']
            rows.append(('Walking link', '%s, ~%d min on foot' % (ST[o]['n'], w['t'])))
    return '<table>' + ''.join('<tr><th>%s</th><td>%s</td></tr>' % (e(k), e(v)) for k, v in rows) + '</table>'


def related_dest(slug, n=4):
    me = next(d for d in CFG['destinations'] if d['slug'] == slug)
    sid = PL[me['main']]['st']
    others = sorted((d for d in CFG['destinations'] if d['slug'] != slug), key=lambda d: km(sid, PL[d['main']]['st']))[:n]
    return '<ul class="links">' + ''.join('<li><a href="{ROOT}destinations/%s/">%s</a></li>' % (d['slug'], e(d['title'])) for d in others) + '</ul>'



def short_lines(ls):
    """'Blue Line' or 'Blue/Yellow/Purple lines', for titles"""
    names = [LINE_NAME[l] for l in ls]
    return names[0] if len(names) == 1 else '/'.join(n.replace(' Line', '') for n in names) + ' lines'


def answer_title(T, kind, main, sid, with_lines=True):
    """a title that answers the search: 'Kingdom Centre Metro Station: Al Urubah (Blue Line), 4 min walk'"""
    t = '%s %s: %s' % (T, 'Tram Stop' if kind == 'stop' else 'Metro Station', ST[sid]['n'])
    if with_lines:
        t += ' (%s)' % short_lines(ST[sid]['lines'])
    if main.get('min') and not main.get('note'):
        t += ', %d min walk' % main['min']
    if len(t) > 75 and with_lines:   # too long for the search results: the lines are on the page anyway
        return answer_title(T, kind, main, sid, False)
    if len(t) > 75 and '(' in T:     # still too long: drop the other name in brackets
        return answer_title(re.sub(r'\s*\(.*?\)', '', T), kind, main, sid, False)
    return t


def answer_desc(T, kind, main, sid, tail):
    d = 'The nearest %s to %s is %s on the %s' % ('tram stop' if kind == 'stop' else 'metro station', T, ST[sid]['n'], ' and '.join(LINE_NAME[l] for l in ST[sid]['lines']))
    if main.get('note'):
        d += ', then by bus or taxi'
    elif main.get('min'):
        d += ', about %d minutes on foot' % main['min']
    return d + '. ' + tail


# ---------------- destination pages ----------------
def destination(d):
    main = PL[d['main']]; sid = main['st']; s = ST[sid]
    path = 'destinations/%s/' % d['slug']
    lines = [l for l in s['lines']]
    line_txt = ' and '.join(LINE_NAME[l] for l in lines)
    kind_word = 'stop' if any(l in ('tram', 'mono') for l in lines) else 'station'
    if d.get('lead'):
        lead = d['lead']
    else:
        lead = 'The nearest %s to %s is %s on the %s.' % (kind_word, main['n'], s['n'], line_txt)
        if main.get('min'):
            lead += ' It is about %d minutes on foot, %s.' % (main['min'], t(main['walk']))
        if other_names(sid):
            lead += ' The station has also been called %s.' % ' and '.join(other_names(sid))
        if main.get('note'):
            lead += ' ' + t(main['note'], s=s['n'])
    body = ['<h1>%s by metro: nearest station and how to get there</h1>' % e(d['title']), '<p class="lead">%s</p>' % e(lead)]
    if any(LINE_KIND[l] in SUSP for l in lines):
        body.append('<div class="warn">%s The routes below show the monorail part for when it reopens; check the operator before you travel.</div>' % e(t('monoSuspended')))
    o0 = d['origins'][0]
    body.append(plan(*((d['main'], o0) if d.get('reverse') else (o0, d['main'])), 'Open on the interactive map'))
    # the places on this page and their walks
    allp = [d['main']] + d['also']
    body.append('<h2>Nearest stop and walking time</h2><div class="scroll"><table><tr><th>Place</th><th>Nearest stop</th><th>On foot</th></tr>')
    for pid in allp:
        p = PL[pid]
        if p.get('note'):
            foot = t(p['note'])
        elif p.get('min'):
            foot = '~%d min, %s' % (p['min'], t(p['walk']))
        else:
            foot = 'Short walk; no reliable time known'
        body.append('<tr><td>%s</td><td>%s (%s)</td><td>%s</td></tr>' % (e(p['n']), e(ST[p['st']]['n']), e(', '.join(LINE_NAME[l] for l in ST[p['st']]['lines'])), e(foot)))
    body.append('</table></div>')
    body.append('<h2>%s</h2>' % ('Getting there' if not d.get('reverse') else 'From the airport'))
    pairs = [(d['main'], o) for o in d['origins']] if d.get('reverse') else [(o, d['main']) for o in d['origins']]
    body.append(routes_table(pairs, None))
    first = pairs[0]
    body.append('<h3>Step by step: %s to %s</h3>' % (e(end_of(first[0])['name']), e(end_of(first[1])['name'])))
    body.append(route_card(*first))
    body.append('<h2>The station</h2><p><b>%s</b></p>' % e(s['n']))
    body.append(station_facts(sid))
    links = station_links(sid)
    links = [x for x in links if x[0] != path]
    body.append('<ul class="links">' + ''.join('<li><a href="{ROOT}%s">%s</a></li>' % (LINE_PAGE[l], e(LINE_NAME[l])) for l in lines) +
                ''.join('<li><a href="{ROOT}%s">%s</a></li>' % (p, e(n)) for p, n in links) + '</ul>')
    kinds = sorted({LINE_KIND[l] for l in lines}, key=['metro', 'tram', 'mono'].index)
    body.append(hours_html(kinds))
    body.append('<h2>Nearby on this map</h2>' + related_dest(d['slug']))
    title = answer_title(d['title'], kind_word, main, sid)
    desc = answer_desc(d['title'], kind_word, main, sid, 'Travel times from the airport and other areas, Nol fare and hours.')
    write(path, frame(path, title, desc, '\n'.join(body), [(path, d['title'])]))


# ---------------- station pages ----------------
def station(cfg):
    sid = cfg['id']; s = ST[sid]
    path = 'stations/%s/' % cfg['slug']
    lines = s['lines']
    xchg = len(lines) > 1
    lead = '%s is %s station on the %s.' % (s['n'], 'an interchange' if xchg else 'a metro', ' and '.join(LINE_NAME[l] for l in lines))
    if xchg:
        lead += ' You can change between the %s here without leaving the station.' % ' and '.join(LINE_NAME[l] for l in lines)
    for w in WALKS:
        if sid in (w['a'], w['b']):
            o = w['b'] if w['a'] == sid else w['a']
            lead += ' %s (%s) is about %d minutes away on foot.' % (ST[o]['n'], ', '.join(LINE_NAME[l] for l in ST[o]['lines']), w['t'])
    if other_names(sid):
        lead += ' Other or former names: %s.' % ', '.join(other_names(sid))
    body = ['<h1>%s metro station</h1>' % e(s['n']), '<p class="lead">%s</p>' % e(lead), station_ctas(sid)]
    body.append('<h2>Station facts</h2>' + station_facts(sid))
    # neighbours on each line
    body.append('<h2>Next stations</h2><ul>')
    seen = set()
    for sv in D['services']:
        if sid not in sv['stops'] or sv['line'] in seen:
            continue
        seen.add(sv['line'])
        st = sv['stops']; i = st.index(sid)
        prev = ST[st[i - 1]]['n'] if i > 0 else None; nxt = ST[st[i + 1]]['n'] if i + 1 < len(st) else None
        body.append('<li>%s: %s</li>' % (e(LINE_NAME[sv['line']]), e(' · '.join(x for x in [prev and ('towards %s: %s' % (ST[st[0]]['n'], prev)), nxt and ('towards %s: %s' % (ST[st[-1]]['n'], nxt))] if x))))
    body.append('</ul>')
    if sid in D['geo']:
        # stations on other lines within 2 km in a straight line (not a walking time: no sourced path)
        others = sorted((km(sid, o), o) for o in D['geo'] if o != sid and not (set(ST[o]['lines']) & set(lines)))
        close = [(d, o) for d, o in others if d <= 2.0][:4]
        if close:
            body.append('<h2>Other lines nearby</h2><ul>')
            for d, o in close:
                body.append('<li>%s (%s), about %.1f km in a straight line%s</li>' % (st_cell(o), e(', '.join(LINE_NAME[l] for l in ST[o]['lines'])), d, ''))
            body.append('</ul>')
    near = [p for p in D['places'] if p['st'] == sid]
    for w in WALKS:
        if sid in (w['a'], w['b']):
            o = w['b'] if w['a'] == sid else w['a']
            near += [p for p in D['places'] if p['st'] == o]
    if near:
        body.append('<h2>Places near the station</h2><ul class="links">')
        for p in near:
            link = DEST_PAGE.get(p['id'])
            nm = '<a href="{ROOT}%s">%s</a>' % (link, e(p['n'])) if link else e(p['n'])
            via = '' if p['st'] == sid else ' (via %s)' % ST[p['st']]['n']
            body.append('<li>%s%s%s</li>' % (nm, e(via), (', ~%d min on foot' % p['min']) if p.get('min') and p['st'] == sid else ''))
        body.append('</ul>')
    body.append('<h2>Routes from %s</h2>' % e(s['n']))
    body.append(routes_table([(sid, x) for x in cfg['to']], None))
    body.append(hours_html(sorted({LINE_KIND[l] for l in lines}, key=['metro', 'tram', 'mono'].index)))
    body.append('<ul class="links">' + ''.join('<li><a href="{ROOT}%s">%s</a></li>' % (LINE_PAGE[l], e(LINE_NAME[l])) for l in lines) + '<li><a href="{ROOT}stations/">All stations and their former names</a></li></ul>')
    title = '%s %s, Dubai: %s%s' % (s['n'], 'Tram Stop' if any(l in ('tram', 'mono') for l in lines) else 'Metro Station', short_lines(lines), (' (formerly %s)' % other_names(sid)[0]) if other_names(sid) else '')
    desc = lead.split('. ')[0] + '. ' + ('Also called %s. ' % ', '.join(other_names(sid)) if other_names(sid) else '') + 'Routes, walking links, fare zone and hours.'
    write(path, frame(path, title, desc, '\n'.join(body), [('stations/', 'Stations'), (path, s['n'])],
                      {"@context": "https://schema.org", "@type": "SubwayStation", "name": s['n'], **({"alternateName": s['f']} if s['f'] else {}),
                       "geo": {"@type": "GeoCoordinates", "latitude": D['geo'][sid][0], "longitude": D['geo'][sid][1]}} if sid in D['geo'] else None))


# ---------------- route pages ----------------
def route_page(r):
    path = 'routes/%s/' % r['slug']
    a, b = r['pairs'][0]
    v, _ = best(a, b)
    A, B = end_of(a), end_of(b)
    f = fare(v)
    uses = ', then '.join(('the ' + LINE_NAME[l]) if l != 'walk' else 'a short walk' for l in lines_of(v))
    lead = 'From %s, take %s to %s: about %d–%d minutes door to door with %s, AED %s with a Silver Nol card.' % (
        A['name'], uses, B['name'], v['time'], v['timeMax'], xf_text(v['xf']), aed(f['silver']))
    body = ['<h1>%s</h1>' % e(r['title']), '<p class="lead">%s</p>' % e(lead), plan(a, b)]
    for i, (x, y) in enumerate(r['pairs']):
        body.append(route_card(x, y, 'From %s to %s' % (end_of(x)['name'], end_of(y)['name'])))
    # fares for this trip
    body.append('<h2>Fare</h2><table><tr><th>Ticket</th><th>Single trip (%d zone%s)</th></tr>' % (f['zones'], '' if f['zones'] == 1 else 's'))
    body.append('<tr><td>Silver Nol card</td><td>AED %s</td></tr><tr><td>Gold Nol card (Gold Class)</td><td>AED %s</td></tr><tr><td>Red ticket (paper)</td><td>AED %s</td></tr></table>' % (aed(f['silver']), aed(f['gold']), aed(f['red'])))
    body.append('<p class="note">Fares by Nol zone, as published by RTA. A single trip is charged by the number of zones it passes through.</p>')
    x, y = r['return']
    body.append('<h2>Return trip</h2>')
    body.append(route_card(x, y, 'From %s to %s' % (end_of(x)['name'], end_of(y)['name'])))
    kinds = sorted({LINE_KIND[l['line']] for p in r['pairs'] for l in best(*p)[0]['legs'] if l['type'] == 'ride'}, key=['metro', 'tram', 'mono'].index)
    body.append(hours_html(kinds))
    title_of = {'destinations/%s/' % d['slug']: d['title'] for d in CFG['destinations']}
    ends = []
    for pr in r['pairs']:
        for tok in pr:
            pg = DEST_PAGE.get(tok)
            if pg and pg not in ends:
                ends.append(pg)
    body.append('<h2>More about these places</h2><ul class="links">' + ''.join('<li><a href="{ROOT}%s">%s by metro</a></li>' % (p, e(title_of[p])) for p in ends) + '</ul>')
    title = '%s: Time, Fare and Steps' % r['title']
    desc = lead
    write(path, frame(path, title, desc, '\n'.join(body), [(path, r['title'])]))


# ---------------- line pages ----------------
def conn(sid, line):
    s = ST[sid]; out = [LINE_NAME[l] for l in s['lines'] if l != line]
    for w in WALKS:
        if sid in (w['a'], w['b']):
            o = w['b'] if w['a'] == sid else w['a']
            out.append('walk to %s (%s), ~%d min' % (ST[o]['n'], ', '.join(LINE_NAME[l] for l in ST[o]['lines']), w['t']))
    return '; '.join(out)


def at_link(sid):
    """opens the app with the map centred on the station and its card open (From here / To here)"""
    return '{ROOT}#at~%s~en' % sid


def map_pin(sid):
    return ' <a class="mapl" href="%s" aria-label="Show %s on the interactive map">map</a>' % (at_link(sid), e(ST[sid]['n']))


def st_cell(sid):
    links = station_links(sid)
    nm = e(ST[sid]['n'])
    return (('<a href="{ROOT}%s">%s</a>' % (links[0][0], nm)) if links else nm) + map_pin(sid)


def station_ctas(sid):
    return ('<p><a class="cta" href="%s">Show on the map</a> <a class="cta alt" href="{ROOT}#%s~~en">Plan a route from here</a> '
            '<a class="cta alt" href="{ROOT}#~%s~en">Plan a route to here</a></p>') % (at_link(sid), sid, sid)


def station_table(ids, line):
    zc = line != 'mono'
    h = ['<div class="scroll"><table><tr><th>#</th><th>Station</th>%s<th>Other or former names</th><th>Connections</th></tr>' % ('<th>Zone</th>' if zc else '')]
    for i, sid in enumerate(ids, 1):
        z = ('<td>%s</td>' % ZONE.get(sid, '')) if zc else ''
        h.append('<tr><td>%d</td><td>%s</td>%s<td>%s</td><td>%s</td></tr>' % (i, st_cell(sid), z, e(', '.join(other_names(sid))), e(conn(sid, line))))
    h.append('</table></div>')
    return '\n'.join(h)


def line_pages():
    R1, R2 = SVC['R1']['stops'], SVC['R2']['stops']
    split = next(i for i, (x, y) in enumerate(zip(R1, R2)) if x != y) - 1
    np = R1[split]
    branch = R2[split + 1:]
    # Red
    path = 'lines/red-line/'
    main_after = R1[split + 1:]
    lead = ('The Red Line runs from %s to %s, with a branch from %s to %s. Trains from %s run either to %s or to %s, so check the destination on the train: '
            'for %s to %s take a train to %s; for %s to %s take a train to %s; to go from one branch to the other, change at %s.') % (
        ST[R1[0]]['n'], ST[R1[-1]]['n'], ST[np]['n'], ST[R2[-1]]['n'], ST[R1[0]]['n'], ST[R1[-1]]['n'], ST[R2[-1]]['n'],
        ST[branch[0]]['n'], ST[branch[-1]]['n'], ST[R2[-1]]['n'], ST[main_after[0]]['n'], ST[main_after[-1]]['n'], ST[R1[-1]]['n'], ST[np]['n'])
    body = ['<h1>Dubai Metro Red Line: stations, branches and hours</h1>', '<p class="lead">%s</p>' % e(lead), plan('at3', 'p_dubai_mall', 'Plan a Red Line trip')]
    body.append('<h2>Main line: %s to %s (%d stations)</h2>' % (e(ST[R1[0]]['n']), e(ST[R1[-1]]['n']), len(R1)))
    body.append(station_table(R1, 'red'))
    body.append('<h2>Expo branch: %s to %s (%d stations after %s)</h2>' % (e(ST[np]['n']), e(ST[R2[-1]]['n']), len(branch), e(ST[np]['n'])))
    body.append(station_table(branch, 'red'))
    body.append(hours_html(['metro']))
    body.append('<h2>Popular trips</h2>' + routes_table([('p_dxb_airport_terminal_3', 'p_dubai_mall'), ('p_dubai_mall', 'p_mall_of_the_emirates'), ('p_dubai_mall', 'p_expo_city_dubai')], None))
    write(path, frame(path, 'Dubai Metro Red Line: Stations, Expo Branch, Map and Hours', lead.split(';')[0] + '.', '\n'.join(body), [(path, 'Red Line')]))
    # Green
    G = SVC['G']['stops']
    path = 'lines/green-line/'
    lead = 'The Green Line runs from %s to %s (%d stations). It meets the Red Line at %s.' % (ST[G[0]]['n'], ST[G[-1]]['n'], len(G), ' and '.join(ST[x]['n'] for x in G if 'red' in ST[x]['lines']))
    body = ['<h1>Dubai Metro Green Line: stations and hours</h1>', '<p class="lead">%s</p>' % e(lead), plan('union', 'p_gold_souk', 'Plan a Green Line trip')]
    body.append('<h2>Stations</h2>' + station_table(G, 'green'))
    body.append(hours_html(['metro']))
    body.append('<h2>Popular trips</h2>' + routes_table([('union', 'p_gold_souk'), ('p_al_fahidi_historical_district', 'p_dubai_mall'), ('creek', 'eand')], None))
    write(path, frame(path, 'Dubai Metro Green Line: Stations, Map and Hours', lead, '\n'.join(body), [(path, 'Green Line')]))
    # Tram
    T, TI = SVC['T']['stops'], SVC['TI']['stops']
    path = 'tram/'
    loop = TI[TI.index('dmt'):] + ['dmt']
    lead = ('The Dubai Tram runs between %s and %s (%d stops). At the JBR end it runs one way round a loop: %s. '
            'The planner takes the loop direction into account, so it may suggest a change at %s or a short walk.') % (
        ST[T[0]]['n'], ST[T[-1]]['n'], len(set(T)), ' → '.join(ST[x]['n'] for x in loop), ST['dmt']['n'])
    body = ['<h1>Dubai Tram: stops, the JBR loop and metro connections</h1>', '<p class="lead">%s</p>' % e(lead), plan('p_dubai_marina_walk', 'p_jbr_the_walk', 'Plan a tram trip')]
    body.append('<h2>Towards %s</h2>' % e(ST[T[-1]]['n']) + station_table(T, 'tram'))
    body.append('<h2>Towards JBR (into the loop)</h2><p>%s</p>' % e(' → '.join(ST[x]['n'] for x in TI)))
    body.append(hours_html(['tram']))
    body.append('<h2>Popular trips</h2>' + routes_table([('p_jbr_the_walk', 'p_dubai_mall'), ('p_dubai_marina_walk', 'p_jbr_the_walk'), ('p_dxb_airport_terminal_3', 'p_jbr_the_walk')], None))
    write(path, frame(path, 'Dubai Tram: Stops, JBR Loop, Metro Links and Hours', '. '.join(lead.split('. ')[:2]) + '.', '\n'.join(body), [(path, 'Dubai Tram')]))
    # Monorail
    M = SVC['M']['stops']
    path = 'palm-monorail/'
    status = ('Status: %s The operator states that the service is temporarily suspended until further notice for maintenance.' % t('monoSuspended')) if 'mono' in SUSP else 'Status: operating.'
    lead = 'The Palm Monorail runs from %s to %s on Palm Jumeirah (%d stations). It is run by a private operator and needs its own ticket; Nol cards are not used.' % (ST[M[0]]['n'], ST[M[-1]]['n'], len(M))
    body = ['<h1>Palm Monorail: status, stations and fares</h1>', '<div class="warn">%s</div>' % e(status) if 'mono' in SUSP else '<p>%s</p>' % e(status), '<p class="lead">%s</p>' % e(lead)]
    body.append('<h2>Stations</h2>' + station_table(M, 'mono'))
    body.append('<p>%s is about %d minutes on foot from the Palm Jumeirah tram stop.</p>' % (ST['palmgw']['n'], next(w['t'] for w in WALKS if {'palmgw', 'pj'} == {w['a'], w['b']})))
    body.append('<h2>Single fares (AED, operator\'s table)</h2><div class="scroll"><table><tr><th>From \\ To</th>' + ''.join('<th>%s</th>' % e(ST[x]['n']) for x in M) + '</tr>')
    for a in M:
        body.append('<tr><th>%s</th>%s</tr>' % (e(ST[a]['n']), ''.join('<td>%s</td>' % ('–' if a == b else mono_fare(a, b)) for b in M)))
    body.append('</table></div><p class="note">%s</p>' % e(t('monoSource')))
    body.append('<h2>Getting to Atlantis</h2><p><a href="{ROOT}destinations/atlantis-the-palm/">Atlantis The Palm by metro, tram and monorail</a></p>')
    write(path, frame(path, 'Palm Monorail: Is It Running? Stations and Fares', status + ' ' + lead.split('. ')[0] + '.', '\n'.join(body), [(path, 'Palm Monorail')]))


# ---------------- stations list ----------------
def stations_list():
    path = 'stations/'
    ids = sorted(ST, key=lambda i: ST[i]['n'].lower())
    renamed = [i for i in ids if other_names(i)]
    lead = 'All %d stations of the Dubai Metro, Dubai Tram and Palm Monorail, with their lines and fare zones. %d of them are also known by another or an earlier name; find the current name below.' % (len(ids), len(renamed))
    body = ['<h1>Dubai Metro stations: new and old names</h1>', '<p class="lead">%s</p>' % e(lead), map_figure()]
    body.append('<h2>Stations with other or former names</h2><div class="scroll"><table><tr><th>Current name</th><th>Other or former names</th><th>Lines</th></tr>')
    for i in renamed:
        body.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (st_cell(i), e(', '.join(other_names(i))), e(', '.join(LINE_NAME[l] for l in ST[i]['lines']))))
    body.append('</table></div>')
    xs = sorted({i for i in ids if len(ST[i]['lines']) > 1}, key=lambda i: ST[i]['n'])
    body.append('<h2>Interchanges and walking links</h2><ul>')
    for i in xs:
        body.append('<li>%s: change between the %s inside the station.</li>' % (st_cell(i), e(' and '.join(LINE_NAME[l] for l in ST[i]['lines']))))
    for w in WALKS:
        body.append('<li>%s and %s: about %d minutes on foot.</li>' % (st_cell(w['a']), st_cell(w['b']), w['t']))
    body.append('</ul>')
    body.append('<h2>All stations A–Z</h2><div class="scroll"><table><tr><th>Station</th><th>Lines</th><th>Zone</th></tr>')
    for i in ids:
        z = '' if ST[i]['lines'] == ['mono'] else ZONE.get(i, '')
        body.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (st_cell(i), e(', '.join(LINE_NAME[l] for l in ST[i]['lines'])), z))
    body.append('</table></div>')
    body.append('<ul class="links">' + ''.join('<li><a href="{ROOT}%s">%s</a></li>' % (LINE_PAGE[l], e(LINE_NAME[l])) for l in ['red', 'green', 'tram', 'mono']) + '</ul>')
    write(path, frame(path, 'Dubai Metro Stations: Full List with Old and New Names', lead, '\n'.join(body), [(path, 'Stations')]))


MAP_IMG = 'dubai-metro-map.png'
MAP_W, MAP_H = 1600, 1560
MAP_ALT = 'Dubai Metro map: Red Line, Green Line, Dubai Tram and Palm Monorail with all stations and interchanges'


def map_figure(link=True):
    img = '<img src="{ROOT}%s" width="%d" height="%d" alt="%s" loading="lazy" style="width:100%%;height:auto;border:1px solid var(--rule);border-radius:12px;background:#fff">' % (MAP_IMG, MAP_W, MAP_H, e(MAP_ALT))
    if link:
        img = '<a href="{ROOT}map/">%s</a>' % img
    return '<figure style="margin:12px 0">%s<figcaption class="note">The whole network on one map. <a href="{ROOT}">Open the interactive map</a> to tap a station and get a route.</figcaption></figure>' % img


def map_page():
    path = 'map/'
    n_st = len(ST)
    G, R1, R2, T, M = SVC['G']['stops'], SVC['R1']['stops'], SVC['R2']['stops'], SVC['T']['stops'], SVC['M']['stops']
    red = len(set(R1) | set(R2))
    lead = ('A schematic map of the Dubai Metro Red Line (%d stations) and Green Line (%d stations), the Dubai Tram (%d stops) and the Palm Monorail (%d stations): '
            '%d stations in all, with current names and every interchange.') % (red, len(G), len(set(T)), len(M), n_st)
    xs = sorted({sid for sid in ST if len(ST[sid]['lines']) > 1}, key=lambda i: ST[i]['n'])
    walks = ['%s and %s (~%d min on foot)' % (ST[w['a']]['n'], ST[w['b']]['n'], w['t']) for w in WALKS]
    body = ['<h1>Dubai Metro map 2026: all lines and stations</h1>', '<p class="lead">%s</p>' % e(lead),
            '<a class="cta" href="{ROOT}">Open the interactive map</a>',
            '<figure style="margin:12px 0"><img src="{ROOT}%s" width="%d" height="%d" alt="%s" style="width:100%%;height:auto;border:1px solid var(--rule);border-radius:12px;background:#fff"><figcaption class="note">%s</figcaption></figure>' % (
                MAP_IMG, MAP_W, MAP_H, e(MAP_ALT), 'Schematic, not to scale. Station names as of September 2026. An unofficial map, not affiliated with RTA.'),
            '<h2>How to read the map</h2><ul>',
            '<li><b>Red Line</b>: %s to %s, with a branch from %s to %s. <a href="{ROOT}lines/red-line/">Red Line stations</a></li>' % (e(ST[R1[0]]['n']), e(ST[R1[-1]]['n']), e(ST['np']['n']), e(ST[R2[-1]]['n'])),
            '<li><b>Green Line</b>: %s to %s. <a href="{ROOT}lines/green-line/">Green Line stations</a></li>' % (e(ST[G[0]]['n']), e(ST[G[-1]]['n'])),
            '<li><b>Dubai Tram</b>: %s to %s, one way round a loop at JBR. <a href="{ROOT}tram/">Tram stops</a></li>' % (e(ST[T[0]]['n']), e(ST[T[-1]]['n'])),
            '<li><b>Palm Monorail</b>: %s to %s%s. <a href="{ROOT}palm-monorail/">Status and fares</a></li>' % (e(ST[M[0]]['n']), e(ST[M[-1]]['n']), ', temporarily suspended' if 'mono' in SUSP else ''),
            '<li><b>Interchanges in one station</b>: %s.</li>' % e(', '.join(ST[x]['n'] for x in xs)),
            '<li><b>Walking links between stations</b> (dotted on the map): %s.</li>' % e('; '.join(walks)),
            '</ul>',
            '<p>Looking for a station by an old name? See <a href="{ROOT}stations/">all stations with their new and old names</a>.</p>',
            '<h2>Open a station on the interactive map</h2><p>Tap a name: the map opens on that station, then choose From here or To here and tap a second station.</p>']
    for title, ids in (('Red Line', R1 + [x for x in R2 if x not in R1]), ('Green Line', G), ('Dubai Tram', [x for i, x in enumerate(T) if x not in T[:i]]), ('Palm Monorail', M)):
        body.append('<h3>%s</h3><p class="stl">%s</p>' % (e(title), ' · '.join('<a href="%s">%s</a>' % (at_link(x), e(ST[x]['n'])) for x in ids)))
    body = body
    ld = {"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": SITE + MAP_IMG, "name": "Dubai Metro, Tram and Palm Monorail map",
          "description": MAP_ALT, "width": MAP_W, "height": MAP_H, "encodingFormat": "image/png"}
    write(path, frame(path, 'Dubai Metro Map 2026: All Lines and Stations (Image and Interactive)', lead, '\n'.join(body), [(path, 'Map')], ld, og_image=MAP_IMG))


def build():
    PAGES.clear()
    stations_list()
    map_page()
    line_pages()
    for d in CFG['destinations']:
        destination(d)
    for s in CFG['stations']:
        station(s)
    for r in CFG['routes']:
        route_page(r)
    return dict(PAGES)


if __name__ == '__main__':
    p = build()
    print('guide pages:', len(p))
    for k in p:
        print(' ', k)
