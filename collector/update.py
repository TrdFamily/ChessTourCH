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
    return list({event["id"]: event for event in events}.values())

def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "ChessTourCH/0.4"})
    with urllib.request.urlopen(request, timeout=25) as response:
        html = response.read(2_000_000).decode("utf-8", "replace")
    events = parse(html)
    if not events:
        raise RuntimeError("Aucun événement détecté : ancien calendrier conservé")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(events)} annonces juniors collectées")

if __name__ == "__main__":
    main()
