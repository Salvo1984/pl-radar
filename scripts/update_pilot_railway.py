#!/usr/bin/env python3
"""Fetch OSM railway geometry around the pilot crossing for GitHub Pages.
This is cartographic information only, not barrier-state information.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.parse
import urllib.request

LAT, LON = 40.8797604, 14.5363296
QUERY = '[out:json][timeout:35];way["railway"~"^(rail|light_rail|narrow_gauge)$"](around:350,40.8797604,14.5363296);out geom;'
ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
data = None
for base in ENDPOINTS:
    try:
        req = urllib.request.Request(
            base + "?" + urllib.parse.urlencode({"data": QUERY}),
            headers={"User-Agent": "PLRadar-OSM-Archive/1.0 (GitHub Pages pilot)", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            candidate = json.load(response)
        if not isinstance(candidate.get("elements"), list):
            raise ValueError("Missing elements array")
        data = candidate
        print("OSM data fetched from", base)
        break
    except Exception as exc:
        print("Failed", base, repr(exc), flush=True)
if data is None:
    raise SystemExit("No OSM data retrieved; leaving prior archive unchanged")

ways = []
for item in data["elements"]:
    if item.get("type") != "way" or not isinstance(item.get("geometry"), list):
        continue
    coords = [[p["lat"], p["lon"]] for p in item["geometry"] if "lat" in p and "lon" in p]
    if len(coords) >= 2:
        ways.append({"id": item["id"], "tags": item.get("tags", {}), "coords": coords})
if not ways:
    raise SystemExit("No railway ways in OSM response; leaving prior archive unchanged")
out = {
    "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "source": "OpenStreetMap / Overpass",
    "pilot": {"lat": LAT, "lon": LON, "osm_node": 324835300},
    "disclaimer": "Nearby railway geometry only. Full station connectivity and barrier state not verified.",
    "ways": ways,
}
target = Path("data/pilot-railway-tracks.json")
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print("Saved", len(ways), "railway ways to", target)
