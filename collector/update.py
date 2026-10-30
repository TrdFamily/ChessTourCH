#!/usr/bin/env python3
"""Extraction prudente des annonces de tournois juniors de Swiss Chess."""
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import urllib.request

SOURCE = "https://swisschess.ch/fr/jugend/turniere/uebersicht-turniere"
OUT = Path(__file__).resolve().parents[1] / "docs" / "tournois.json"
DATE = re.compile(r"(\d{1,2})[./ -]+(\d{1,2})[./ -]+(20\d{2})")

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self.skip += 1
        if tag in ("p", "div", "li", "h2", "h3", "br", "time"):
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self.skip:
            self.skip -= 1
        if tag in ("p", "div", "li", "h2", "h3", "time"):
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def parse(html, today=None):
    today = today or date.today()
    parser = Parser()
    parser.feed(html)
    lines = [re.sub(r"\s+", " ", x).strip() for x in "".join(parser.parts).splitlines()]
    lines = [x for x in lines if x]
    start = next((i for i, x in enumerate(lines) if x in ("Prochains tournois juniors", "Bevorstehende Jugendturniere")), None)
    if start is None:
        return []
    events = []
    for i in range(start + 1, len(lines) - 1):
        match = DATE.search(lines[i])
        if not match:
            continue
        try:
            day = date(int(match[3]), int(match[2]), int(match[1]))
        except ValueError:
            continue
        if day < today:
            continue
        title = lines[i + 1]
        if len(title) < 5 or len(title) > 150 or DATE.search(title) or "Liechtenstein" in title:
            continue
        events.append({
            "id": "ssb-junior-" + day.isoformat() + "-" + re.sub(r"[^a-z0-9]+", "-", title.lower())[:45],
            "title": title, "date": day.isoformat(), "endDate": day.isoformat(),
            "city": title.split(":", 1)[0] if ":" in title else "",
            "category": "Junior", "tempo": "", "lat": None, "lon": None,
            "adultPrice": None, "juniorPrice": None, "registrationUrl": None,
            "url": None, "discoveryUrl": SOURCE, "source": SOURCE, "status": "À vérifier auprès de l'organisateur"
        })
    # Tournoi local confirme par l'annonce regionale RFJ du 19 octobre 2026.
    local_events = [{
        "id": "courroux-echecs-aux-loups-2026-11-08",
        "title": "2e tournoi junior Échecs aux Loups",
        "date": "2026-11-08", "endDate": "2026-11-08",
        "city": "Courroux (près de Delémont)",
        "address": "Halle de gymnastique, Courroux",
        "time": "14h00–17h30", "category": "Junior",
        "ageCategories": "U10, U15, U20",
        "tempo": "", "lat": None, "lon": None,
        "adultPrice": None, "juniorPrice": None,
        "registrationUrl": None,
        "url": None, "discoveryUrl": "https://www.rfj.ch/rfj/Actualite/Region/20261019-La-passion-des-echecs-version-jeune-a-Courroux.html",
        "source": "https://www.rfj.ch/rfj/Actualite/Region/20261019-La-passion-des-echecs-version-jeune-a-Courroux.html",
        "status": "Horaire et lieu confirmés ; prix et inscription à confirmer"
    }]
    # Donnees de l'organisateur et des annonces evenementielles verifiees.
    # Ne jamais deduire une adresse du domicile d'un club ni du centre-ville.
    verified = {
        "Winterthur: Jugendstadtmeisterschaft": {
            "city": "Winterthur",
            "venue": "Kirchgemeindehaus Veltheim",
            "address": "Feldstrasse 6, 8400 Winterthur",
            "addressVerified": True,
            "url": "https://www.sgwinterthur.ch/wjsm2026/",
            "source": "https://www.sgwinterthur.ch/wjsm2026/",
        },
        "2. Qualiturnier in Lugano": {
            "date": "2026-11-06", "endDate": "2026-11-08",
            "city": "Lugano", "venue": "Palazzo dei Congressi, salle B",
            "address": "Piazza dell'Indipendenza 4, 6900 Lugano",
            "addressVerified": True, "time": "Vendredi 18h30 ; samedi 9h30 et 14h30 ; dimanche 9h et 13h30",
            "juniorPrice": 50,
            "url": "https://swisschess.ch/fr/news/68-november-in-lugano-zweites-quali-turnier-zur-u10u12u14u16u18-meisterschaft-2027",
            "source": "https://swisschess.ch/fr/news/68-november-in-lugano-zweites-quali-turnier-zur-u10u12u14u16u18-meisterschaft-2027",
        }
    }
    for event in events:
        for name, details in verified.items():
            if name.lower() in event["title"].lower():
                event.update(details)
    local_events[0].update({
        "venue": "Halle de gymnastique Général-Guisan",
        "address": "Rue du Général-Guisan 3, 2822 Courroux", "addressVerified": True,
        "url": None
    })
    # Annonces de clubs hors liste federale, verifiees sur leurs pages.
    local_events.extend([
        {"id":"sc-reti-schoenau-rapid-u12-2026-11-29","title":"3. Schönau Rapidturnier U12",
         "date":"2026-11-29","endDate":"2026-11-29","city":"Zürich",
         "venue":"Saal der Baugenossenschaft Schönau Zürich",
         "address":"Schönauring 78, 8052 Zürich","addressVerified":True,
         "time":"Contrôle jusqu'à 13h15 ; début 13h30 ; remise des prix vers 17h00",
         "juniorPrice":10,"adultPrice":None,"category":"Junior","tempo":"Rapid, 8 min + 4 sec/coup",
         "url":"https://www.screti.ch/index.php/jugendschach/schonau-rapidturnier-u12.html",
         "source":"https://www.screti.ch/index.php/jugendschach/schonau-rapidturnier-u12.html",
         "registrationUrl":"mailto:roman@schnelli.com"},
        {"id":"chessmates-degersheim-herbst-r2-2026-11-04",
         "title":"Degersheimer Herbstturnier, Runde 2",
         "date":"2026-11-04","endDate":"2026-11-04","city":"Degersheim",
         "venue":"Restaurant Rose","address":"Bergstrasse 1, 9113 Degersheim",
         "addressVerified":True,"time":None,"juniorPrice":None,"adultPrice":None,
         "category":"Adultes","tempo":"","url":None,"discoveryUrl":"https://chessmates.live/turniere",
         "source":"https://chessmates.live/turniere"}
    ])
    events.extend(event for event in local_events if event["date"] >= today.isoformat())
    return list({event["id"]: event for event in events}.values())

import urllib.parse
import xml.etree.ElementTree as ET
import unicodedata

def keywords(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(x for x in s if not unicodedata.combining(x))
    return set(re.findall(r"[a-z0-9]{4,}", s)) - {"open","chess","schach","2026","2027","turnier","tournoi","rapid","runde"}

BLOCKED_HOSTS = ("chessmates.live", "bing.com", "google.com", "facebook.com",
                 "instagram.com", "chess-results.com", "swisschess.ch",
                 "lichess.org", "youtube.com", "wikipedia.org", "tripadvisor.com",
                 "weforum.org", "booking.com", "myswitzerland.com")

def valid_organizer_url(url):
    from urllib.parse import urlsplit
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        return (parts.scheme == "https" and bool(host)
                and not any(host == x or host.endswith("." + x) for x in BLOCKED_HOSTS)
                and not re.search(r"/(turniere|tournois|calendar|kalender|events)/?$", parts.path, re.I))
    except ValueError:
        return False

def search_bing(query):
    feed = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)
    req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        root = ET.fromstring(response.read(250000))
    return [(x.findtext("link") or "", x.findtext("title") or "")
            for x in root.findall(".//item")]

def search_duckduckgo(query):
    """Decode DuckDuckGo's outbound result links."""
    req = urllib.request.Request(
        "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query),
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as response:
        html = response.read(300000).decode("utf-8", "replace")
    links = re.findall(r'uddg=([^& ]+)', html)
    return [(urllib.parse.unquote(html_unescape(x)), "") for x in links]


def html_unescape(value):
    from html import unescape
    return unescape(value)

def discover_candidates(event):
    """Search original-language names across two providers and rank potential organizers."""
    title = re.sub(r"\\s+", " ", event["title"]).strip()
    year = event["date"][:4]
    city = (event.get("city") or "").strip()
    queries = [
        f'"{title}" {year}',
        f'{title} {year} {city} anmeldung inscription',
        f'{title} {year} schach échecs torneo'
    ]
    base = keywords(title)
    found = {}
    for query in queries:
        for provider in (search_bing, search_duckduckgo):
            try:
                results = provider(query)
            except (OSError, ValueError, ET.ParseError):
                continue
            for url, label in results:
                if not valid_organizer_url(url):
                    continue
                from urllib.parse import urlsplit
                slug = urllib.parse.unquote(urlsplit(url).path.replace("-", " ").replace("_", " "))
                matched = len(base & keywords(label + " " + slug))
                if not base or matched < min(2, len(base)):
                    continue
                if len(base) == 1 and title.lower() not in (label + " " + slug).lower():
                    continue
                score = matched * 3
                if year in (label + url):
                    score += 2
                if city and keywords(city) & keywords(label + url):
                    score += 1
                found[url] = max(score, found.get(url, 0))
            if len(found) >= 8:
                break
        if len(found) >= 8:
            break
    return [{"url": url, "title": "Candidat à vérifier", "score": score}
            for url, score in sorted(found.items(), key=lambda pair: -pair[1])[:6]]

class PageText(HTMLParser):
    """Extract visible text and safe absolute registration links."""
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
        self.skip = 0
        self.href = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "nav", "footer"):
            self.skip += 1
        if tag in ("p", "div", "h1", "h2", "h3", "li", "br", "tr"):
            self.parts.append("\n")
        if tag == "a":
            self.href = attrs.get("href")
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self.skip:
            self.skip -= 1
        if tag == "a":
            self.href = None
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.href and re.search(r"inscri|anmeld|registr|teilnehm", data, re.I):
                self.links.append(self.href)

def inspect_candidate(event, url):
    """Only promote a result if the actual page corroborates the edition and title."""
    from urllib.parse import urljoin, urlsplit
    if not valid_organizer_url(url):
        return None
    host = urlsplit(url).hostname or ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ChessTourCH/0.5"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if "text/html" not in response.headers.get("Content-Type", ""):
                return None
            raw = response.read(350000).decode("utf-8", "replace")
    except (OSError, ValueError):
        return None
    parser = PageText()
    parser.feed(raw)
    text = re.sub(r"\s+", " ", " ".join(parser.parts))
    event_words = keywords(event["title"])
    page_words = keywords(text[:30000])
    if not event_words or len(event_words & page_words) < max(1, min(2, len(event_words))):
        return None
    # A year alone is not sufficient: require the event's day/month/year or ISO date.
    d = date.fromisoformat(event["date"])
    formats = (d.isoformat(), f"{d.day}.{d.month}.{d.year}", f"{d.day:02d}.{d.month:02d}.{d.year}",
               f"{d.day}/{d.month}/{d.year}", f"{d.day:02d}/{d.month:02d}/{d.year}")
    if not any(x in text or x in raw for x in formats):
        return None
    # Never promote a generic index or news search results page.
    if re.search(r"/(turniere|tournois|calendar|kalender|events)/?$", urlsplit(url).path, re.I):
        return None
    result = {"url": url, "dataQuality": "official_page", "verifiedBy": "automated_page_match"}
    for href in parser.links:
        link = urljoin(url, href)
        if link.startswith("https://") and urlsplit(link).hostname == host:
            result["registrationUrl"] = link
            break
        if link.startswith("mailto:"):
            result["registrationUrl"] = link
            break
    # Extract only an explicitly labelled single admission fee, with currency.
    fee = re.search(r"(?:Startgeld|Teilnahmegebühr|Inscription|Frais d.inscription)\s*[:–-]?\s*(?:CHF|Fr\.?|SFr\.?)\s*(\d{1,3})(?!\d)", text, re.I)
    if fee:
        result["feeCandidate"] = "CHF " + fee.group(1) + " (catégorie à confirmer)"
    return result

ADDRESS_RE = re.compile(
    r"(?i)(?:rue|route|avenue|av\\.|chemin|place|quai|boulevard|impasse|strasse|straße|weg|gasse|via|piazza)"
    r"\\s+[A-Za-zÀ-ÿ0-9'’ .-]{3,65}?\\s*,?\\s*\\b\\d{1,3}[a-zA-Z]?\\b"
    r"(?:\\s*[,;-]?\\s*\\b\\d{4}\\s+[A-Za-zÀ-ÿ .-]{2,40})?")
POSTAL_RE = re.compile(r"\\b[1-9]\\d{3}\\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .-]{2,35}")

def extract_address_candidates(text, city=""):
    """Return evidence, not guesses. Preserve original excerpts for review."""
    candidates = []
    for match in ADDRESS_RE.finditer(text):
        raw = re.sub(r"\\s+", " ", match.group(0)).strip(" ,;.-")
        context = text[max(0, match.start()-110):min(len(text), match.end()+110)]
        nearby = bool(re.search(r"(?i)lieu|adresse|salle|halle|local|ort|spielort|turnierort|adresse|venue", context))
        postcode = bool(POSTAL_RE.search(context))
        score = int(nearby)*3 + int(postcode)*2 + int(bool(city and city.lower() in context.lower()))
        candidates.append({"address": raw, "evidence": re.sub(r"\\s+", " ", context)[:220], "score": score})
    return sorted(candidates, key=lambda x: -x["score"])[:5]

def inspect_known_page(event):
    """Inspect known organizer announcements too, including first-page PDF attachments."""
    from urllib.parse import urljoin, urlsplit
    url = event.get("url")
    if not url or not url.startswith("https://"):
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ChessTourCH/0.6"})
        with urllib.request.urlopen(req, timeout=12) as response:
            if "text/html" not in response.headers.get("Content-Type", ""):
                return
            raw = response.read(650000).decode("utf-8", "replace")
    except (OSError, ValueError):
        return
    parser = PageText()
    parser.feed(raw)
    text = re.sub(r"\\s+", " ", " ".join(parser.parts))
    candidates = extract_address_candidates(text, event.get("city", ""))
    # Read PDFs linked by this exact event page, prioritizing invitations and rules.
    pdfs = re.findall(r"""href=["']([^"']+\\.pdf(?:\\?[^"']*)?)["']""", raw, re.I)
    for href in pdfs[:3]:
        pdf_url = urljoin(url, html_unescape(href))
        if urlsplit(pdf_url).hostname != urlsplit(url).hostname:
            continue
        try:
            from io import BytesIO
            from pypdf import PdfReader
            req = urllib.request.Request(pdf_url, headers={"User-Agent": "ChessTourCH/0.6"})
            with urllib.request.urlopen(req, timeout=12) as response:
                pdf = response.read(3000000)
            reader = PdfReader(BytesIO(pdf))
            first_page = (reader.pages[0].extract_text() or "") if reader.pages else ""
            for candidate in extract_address_candidates(first_page, event.get("city", "")):
                candidate["source"] = pdf_url + "#page=1"
                candidate["score"] += 2
                candidates.append(candidate)
        except (OSError, ValueError, ImportError, Exception):
            continue
    candidates.sort(key=lambda x: -x["score"])
    if candidates:
        event["addressCandidates"] = candidates[:5]
        # Avoid publishing an unverified address: review the page evidence first.
    event["lastAddressScan"] = datetime.now(timezone.utc).isoformat()

def enrich_candidates(events):
    # Persist per-event search attempts in JSON, so the workflow does not retry
    # the same first twenty events after each fresh GitHub Actions checkout.
    unresolved = [e for e in events if not e.get("url")]
    batch = sorted(unresolved, key=lambda e: (e.get("lastCandidateSearch", ""), e.get("date", "")))[:12]
    for event in batch:
        found = discover_candidates(event)
        event["lastCandidateSearch"] = datetime.now(timezone.utc).isoformat()
        event["officialCandidates"] = found
        for candidate in found:
            verified = inspect_candidate(event, candidate["url"])
            if verified:
                # Keep an existing registration URL; never overwrite verified data.
                for key, value in verified.items():
                    if not event.get(key):
                        event[key] = value
                break
    return events

def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "ChessTourCH/0.4"})
    with urllib.request.urlopen(request, timeout=25) as response:
        html = response.read(2_000_000).decode("utf-8", "replace")
    events = parse(html)
    if not events:
        raise RuntimeError("Aucun événement détecté : ancien calendrier conservé")
    # Merge with previously discovered club and adult events.
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        merged = {e["id"]: e for e in previous if e.get("date", "") >= date.today().isoformat()}
        for event in events:
            existing = merged.get(event["id"], {})
            merged[event["id"]] = {**event, **{k: v for k, v in existing.items() if v is not None and v != ""}}
        events = sorted(merged.values(), key=lambda e: e["date"])
    for event in events:
        url = event.get("url") or ""
        if url in (SOURCE, "https://chessmates.live/turniere") or "rfj.ch/rfj/Actualite/" in url:
            event["discoveryUrl"] = url
            event["url"] = None
        event["dataQuality"] = "official_page" if event.get("url") else ("organizer_only" if event.get("organizerUrl") else "needs_official_page")
    events = enrich_candidates(events)
    known = sorted([e for e in events if e.get("url") and not e.get("addressVerified")],
                   key=lambda e: (0 if "grand prix de payerne" in e.get("title", "").lower() else 1,
                                  e.get("lastAddressScan", ""), e.get("date", "")))[:8]
    for event in known:
        inspect_known_page(event)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(events)} annonces juniors collectées")

if __name__ == "__main__":
    main()
