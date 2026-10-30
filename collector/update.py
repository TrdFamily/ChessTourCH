#!/usr/bin/env python3
"""Extraction prudente des annonces de tournois juniors de Swiss Chess."""
from datetime import date
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
            "url": SOURCE, "source": SOURCE, "status": "À vérifier auprès de l'organisateur"
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
        "url": "https://www.rfj.ch/rfj/Actualite/Region/20261019-La-passion-des-echecs-version-jeune-a-Courroux.html",
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
        "url": "https://www.rfj.ch/rfj/Actualite/Region/20261019-La-passion-des-echecs-version-jeune-a-Courroux.html"
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
         "category":"Adultes","tempo":"","url":"https://chessmates.live/turniere",
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

def discover_candidates(event):
    query = event["title"] + " " + event["date"][:4] + " chess tournament organizer"
    feed = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            root = ET.fromstring(response.read(250000))
    except (OSError, ValueError, ET.ParseError):
        return []
    result = []
    base = keywords(event["title"])
    for item in root.findall(".//item"):
        url = item.findtext("link") or ""
        title = item.findtext("title") or ""
        snippet = item.findtext("description") or ""
        if not url.startswith("https://") or any(x in url.lower() for x in ("chessmates.live","bing.com","google.com","facebook.com","instagram.com")):
            continue
        if len(base & keywords(title + " " + snippet)) < min(2,len(base)):
            continue
        if event["date"][:4] not in (title + " " + snippet + " " + url):
            continue
        result.append({"url":url,"title":title})
        if len(result) >= 3:
            break
    return result

def enrich_candidates(events):
    # Search is a lead, never proof: no automatic assignment to the official URL.
    for event in [e for e in events if not e.get("url") and not e.get("officialCandidates")][:20]:
        found = discover_candidates(event)
        if found:
            event["officialCandidates"] = found
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
    events = enrich_candidates(events)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(events)} annonces juniors collectées")

if __name__ == "__main__":
    main()
