# Dubai Metro Map

An unofficial, free map and journey planner for the Dubai Metro, Dubai Tram and Palm Monorail.

**Live site: https://dubaimetro.fyi**

Type a place or a station (or tap a popular place) and the planner shows the route with every change, the walking parts, an estimated travel time and the Nol fare. It runs in the browser on phones and computers; there is nothing to install and no account. Visits are counted anonymously with [GoatCounter](https://www.goatcounter.com/) (no cookies, no personal data); the statistics are at https://dubaimetro.goatcounter.com.

This is an independent, non-commercial project. It is not affiliated with RTA, and it does not use RTA or Dubai Metro logos.

## Languages

Each language has its own page, so search engines can show people the version in their language. The English page follows the visitor's saved or browser language; the others always open in their own language.

| Language | Address |
|---|---|
| English | https://dubaimetro.fyi/ |
| हिन्दी (Hindi) | https://dubaimetro.fyi/hi.html |
| العربية (Arabic) | https://dubaimetro.fyi/ar.html |
| اردو (Urdu) | https://dubaimetro.fyi/ur.html |
| Русский (Russian) | https://dubaimetro.fyi/ru.html |
| Deutsch (German) | https://dubaimetro.fyi/de.html |
| 中文 (Chinese) | https://dubaimetro.fyi/zh.html |
| Français (French) | https://dubaimetro.fyi/fr.html |
| Filipino | https://dubaimetro.fyi/tl.html |
| বাংলা (Bengali) | https://dubaimetro.fyi/bn.html |

## What it does

- Place-to-place routes across the Red and Green Lines, the Expo branch, the Dubai Tram and the Palm Monorail, showing the fastest route, plus a one-line option with fewer changes when it takes at most 5 minutes longer.
- Step-by-step directions, estimated travel time (with typical waiting time), estimated Nol fare by zone, and opening-hours warnings for late trips.
- About 40 popular places (airport terminals, Dubai Mall, Burj Khalifa, Marina, JBR, Atlantis, souks, Expo City and more), with walking notes where the connection is well known.
- Sharing: copy link, WhatsApp, QR code and a trip card. Every route has its own link.
- A built-in "Report a problem" form that opens a GitHub issue with the route details filled in.
- Works on phones (bottom sheet that folds to one line) and computers, in light and dark mode.
- "Nearest station to me": the location button in the From field picks the closest station and shows the walking time. The location stays on the device.
- Works offline after the first visit, and can be installed on a phone's home screen like an app.

## Data and accuracy

- **Run times** between stations come from the RTA GTFS timetable (November 2021 edition, archived by Transitland). Track and stations have not changed since; travel times are estimates, not real-time.
- **Station names, lines, fare zones and connections** are checked against the RTA rail network map published on 25 September 2026, including the Etihad Rail connection at Jumeirah Golf Estates (Al Yalayis Station) and the bus link to Airport Terminal 2.
- **Fares and opening hours** come from RTA announcements and public sources (2025–2026). Hours change during Ramadan and on public holidays.
- **Palm Monorail** is run by a private operator and is not part of Nol; its status and ticket prices come from the operator's website. It is currently shown as temporarily suspended.
- **Walking times** are rough estimates and are marked as such.
- **Station coordinates** (for "nearest station") come from the same GTFS feed; the four Palm Monorail stations are approximate.

The current RTA timetable is published on Dubai Pulse (dataset `rta_gtfs-open`), where access is granted on request.

## Report a problem

Use the **Report a problem** button on the site, or open an issue here: https://github.com/thinkbig-code/dubai-metro/issues

## Files

| File | Purpose |
|---|---|
| `index.html`, `hi.html`, `ar.html`, `ur.html`, `ru.html`, `de.html`, `zh.html`, `fr.html`, `tl.html`, `bn.html` | The whole app, one page per language. Each file is self-contained (map, data, translations, code). |
| `og-image.png` | Preview image for links shared in WhatsApp, Telegram and social networks. |
| `manifest.webmanifest`, `icon-192.png`, `icon-512.png` | Lets the site be installed on a phone like an app. |
| `sw.js` | Service worker for offline use: pages are fetched fresh when online and the last copy is used offline. Generated from `tools/sw.template.js`. |
| `apple-touch-icon.png` | Icon shown when the site is added to a phone's home screen. The browser tab icon is built into each page. |
| `dubai-metro-map.png` | The whole network as a picture, for Google Images and sharing. Drawn by the app itself with `tools/render_map.js`. |
| `map/`, `stations/`, `lines/`, `tram/`, `palm-monorail/`, `destinations/`, `routes/` | English guide pages for search engines (22 pages, including the map image page): stations with old and new names, the lines, three station pages, ten places and three routes. Each page hands off to the planner or opens a station on the map. |
| `sitemap.xml`, `robots.txt` | For search engines; the sitemap lists the ten language pages and the guide pages. |
| `CNAME` | Connects the custom domain `dubaimetro.fyi` to GitHub Pages. Do not delete it. |

The ten pages are generated from one source file, so an update always changes all ten together:

| Path | Purpose |
|---|---|
| `src/dubai-metro.html` | The single source of the app: map, data, routing, all ten interface languages. Edit this file, not the generated pages. |
| `tools/build.py` | Builds the ten language pages, `sitemap.xml`, `robots.txt`, `manifest.webmanifest` and `sw.js` from the source. |
| `tools/sw.template.js` | Source of `sw.js`; the build adds a version stamp so phones pick up updates. |
| `tools/seo_texts.py` | Per-language page titles, descriptions and the "About this map" text. |
| `tools/seo_config.json` | Which guide pages exist (destinations, stations, routes) and which routes each one shows. A page exists only if it is listed here. |
| `tools/export_data.js` | Exports the app's data and the routes the guide pages need to `tools/seo_data.json`, using the app's own router. Needs Node and Playwright. |
| `tools/seo_data.json` | The exported data. Committed, so the build itself needs only Python. |
| `tools/render_map.js` | Renders `dubai-metro-map.png` from the app's own map. Needs Node and Playwright. |
| `tools/seo_pages.py` | Builds the guide pages from the two files above; called by `build.py`. No fact on a guide page is typed by hand. |

To rebuild after a change (Python 3, no extra packages):

```
python3 tools/build.py
```

If the change touches the network data (stations, places, walking times, fares, hours) or `tools/seo_config.json`, export the data first so the guide pages match the planner:

```
node tools/export_data.js && python3 tools/build.py
```

If station names or the map drawing change, also redraw the map picture (set the date of the names if it changed): `NAMES_AS_OF="September 2026" node tools/render_map.js`.

## IndexNow (Bing, Yandex and others)

After every push to `main` that changes a page, the GitHub Actions workflow `.github/workflows/indexnow.yml` waits two minutes for GitHub Pages to publish, then sends the changed page addresses to IndexNow, so Bing, Yandex, Seznam and Naver crawl them soon. Google does not use IndexNow; it reads `sitemap.xml`. To send every page in the sitemap, run the workflow by hand: Actions → IndexNow → Run workflow. The key is the file `db8803a2bf36307407eb5b4f24516cad.txt` in the site root; `tools/indexnow.py` does the sending.

## Usage events

The site sends anonymous events to GoatCounter (dubaimetro.goatcounter.com) as `event/a/b` with the interface language and a detail in the title: `route` (with where the trip came from: search, popular, map, link, geo, swap or `landing:<guide page>`), `place` and `station` (picked in the search, and whether by name, alias or former name), `noresult` (search text that found nothing, shortened and dropped if it looks like a number or e-mail), `view` (route option or details), `share`, `report` and `geo`. Only ids from the app's data are sent: no coordinates, no report text, nothing about the person.

Events for the map and station-first use:

- `map_station_click/<station>`: a station tapped on the map; the title adds where the visitor came from (`home` or `landing:<guide page>`) and `phone` or `desktop` (from screen width only).
- `route_from_station_click/<station>` and `route_to_station_click/<station>`: From here / To here in a station card (a place picked from the card is sent as the second part).
- `station_pair_route_search/<from>/<to>`: a route with a station at both ends.
- `station_link/at|from|to/<station>`: the app opened from a one-station link.
- Every `route` event also carries `first_<mode>`: how the page view started (`map`, `station_search`, `place_search`, `popular`, `geo`, `link`, `landing`, `swap`).

## Links into the app

- `#<from>~<to>~<lang>`: a route (stations or places).
- `#at~<station>~<lang>`: the map centred on the station with its card open (From here / To here).
- `#<station>~~<lang>` or `#~<station>~<lang>`: one end filled in, the other left for a tap or a search.

Guide pages use these: every station name has a small "map" link, station pages have Show on the map / Plan a route from here / Plan a route to here, and /map/ lists every station as a link that opens it on the map.

To build for another address (for example a new domain), set `SITE`: `SITE=https://example.com/ python3 tools/build.py`, then update `CNAME`.

## Hosting

- **GitHub Pages**, branch `main`, folder `/ (root)`, with **Enforce HTTPS** turned on.
- **Domain:** `dubaimetro.fyi`, registered at Porkbun. DNS records:
  - `A` `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  - `AAAA` `@` → `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
  - `CNAME` `www` → `thinkbig-code.github.io`
  - `TXT` `@` → `google-site-verification=…` (keeps Google Search Console verified; do not remove)
- Old links to `thinkbig-code.github.io/dubai-metro/` redirect to the new domain automatically.
- **Google Search Console:** domain property `dubaimetro.fyi`, sitemap `https://dubaimetro.fyi/sitemap.xml` submitted.

## How updates are made

1. A change is prepared and published as a preview first.
2. It is checked on a phone and a computer.
3. Only after that is it committed here and goes live (usually within 1–2 minutes).

The source is `src/dubai-metro.html`; after editing it, run `python3 tools/build.py` and commit the source together with the regenerated pages, `sw.js` and `manifest.webmanifest`. Each build gives `sw.js` a new version stamp, so phones that use the site offline pick up the update: online visitors get the new version at once, and an installed copy switches to it from the second launch after the update.

## Maintenance (every 2–3 months, about 30 minutes)

1. **Station names.** Check for renamed stations (search "Dubai Metro station renamed"). Old names stay searchable.
2. **Fares and hours.** Compare with RTA.
3. **Palm Monorail.** Check whether it is running again, and its ticket prices.
4. **RTA network map.** Compare with the latest PDF on rta.ae.
5. **Station coordinates.** If a station moves or a new one opens (for example the Blue Line), add its coordinates to `GEO` in the source, or "nearest station" will not know it.
6. **Self-test.** Open `https://dubaimetro.fyi/#selftest`, then the browser console (F12 → Console on a computer). It should end with `VALIDATION: N/N passed` and `ITINERARIES: 10/10 passed`. Any `FAIL` line means something broke.

### Quick phone check after a bigger update

- A route from the airport to Dubai Mall shows time, fare and steps.
- A copied link opens the same route and language on another phone.
- WhatsApp, QR code and the trip card work.
- The panel folds to one line with the handle and opens again.
- Arabic and Urdu read right to left without cut-off letters; Hindi and Chinese show no empty boxes.
- Dark mode is readable; the map pans and zooms with two fingers.
- The location button in the From field fills in the nearest station (allow location when the phone asks).
- After one visit, the site opens in airplane mode and still builds routes.
- "Add to Home screen" (Android: Chrome menu; iPhone: Safari Share) adds the map-pin icon and opens without the address bar.
- Line names appear at the ends of each line and follow the language.
