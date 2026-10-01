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

## What it does

- Place-to-place routes across the Red and Green Lines, the Expo branch, the Dubai Tram and the Palm Monorail, with up to three options (fastest, fewer changes, least walking) and a short "why this route" note.
- Step-by-step directions, estimated travel time (with typical waiting time), estimated Nol fare by zone, and opening-hours warnings for late trips.
- About 40 popular places (airport terminals, Dubai Mall, Burj Khalifa, Marina, JBR, Atlantis, souks, Expo City and more), with walking notes where the connection is well known.
- "Explore Dubai": ten ready-made day trips that open as routes.
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
| `index.html`, `hi.html`, `ar.html`, `ur.html`, `ru.html`, `de.html`, `zh.html`, `fr.html` | The whole app, one page per language. Each file is self-contained (map, data, translations, code). |
| `og-image.png` | Preview image for links shared in WhatsApp, Telegram and social networks. |
| `manifest.webmanifest`, `icon-192.png`, `icon-512.png` | Lets the site be installed on a phone like an app. |
| `sw.js` | Service worker for offline use: pages are fetched fresh when online and the last copy is used offline. Generated from `tools/sw.template.js`. |
| `apple-touch-icon.png` | Icon shown when the site is added to a phone's home screen. The browser tab icon is built into each page. |
| `sitemap.xml`, `robots.txt` | For search engines; the sitemap lists all eight language pages. |
| `CNAME` | Connects the custom domain `dubaimetro.fyi` to GitHub Pages. Do not delete it. |

The eight pages are generated from one source file, so an update always changes all eight together:

| Path | Purpose |
|---|---|
| `src/dubai-metro.html` | The single source of the app: map, data, routing, all eight interface languages. Edit this file, not the generated pages. |
| `tools/build.py` | Builds the eight language pages, `sitemap.xml`, `robots.txt`, `manifest.webmanifest` and `sw.js` from the source. |
| `tools/sw.template.js` | Source of `sw.js`; the build adds a version stamp so phones pick up updates. |
| `tools/seo_texts.py` | Per-language page titles, descriptions and the "About this map" text. |

To rebuild after a change (Python 3, no extra packages):

```
python3 tools/build.py
```

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

## Maintenance (every 2–3 months, about 30 minutes)

1. **Station names.** Check for renamed stations (search "Dubai Metro station renamed"). Old names stay searchable.
2. **Fares and hours.** Compare with RTA.
3. **Palm Monorail.** Check whether it is running again, and its ticket prices.
4. **RTA network map.** Compare with the latest PDF on rta.ae.
5. **Self-test.** Open `https://dubaimetro.fyi/#selftest`, then the browser console (F12 → Console on a computer). It should end with `VALIDATION: N/N passed` and `ITINERARIES: 10/10 passed`. Any `FAIL` line means something broke.

### Quick phone check after a bigger update

- A route from the airport to Dubai Mall shows time, fare and steps.
- A copied link opens the same route and language on another phone.
- WhatsApp, QR code and the trip card work.
- The panel folds to one line with the handle and opens again.
- Arabic and Urdu read right to left without cut-off letters; Hindi and Chinese show no empty boxes.
- Dark mode is readable; the map pans and zooms with two fingers.
