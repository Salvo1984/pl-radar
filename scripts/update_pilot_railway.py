#!/usr/bin/env python3
"""Fetch OSM railway geometry around the pilot crossing for GitHub Pages.
This is cartographic information only, not barrier-state information.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

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
    # Fallback: official OSM map API, small geographic bounding box.
    # This API returns XML nodes and ways rather than Overpass JSON.
    bbox = "14.5322,40.8768,14.5405,40.8827"
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=" + bbox
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PLRadarPilotRailway/1.0", "Accept": "application/xml"})
        with urllib.request.urlopen(req, timeout=45) as response:
            root = ET.fromstring(response.read())
        nodes = {n.attrib["id"]: (float(n.attrib["lat"]), float(n.attrib["lon"])) for n in root.findall("node")}
        elements = []
        for way in root.findall("way"):
            tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
            if tags.get("railway") not in ("rail", "light_rail", "narrow_gauge"):
                continue
            geometry = [{"lat": nodes[nd.attrib["ref"]][0], "lon": nodes[nd.attrib["ref"]][1]} for nd in way.findall("nd") if nd.attrib["ref"] in nodes]
            if len(geometry) >= 2:
                elements.append({"type": "way", "id": int(way.attrib["id"]), "tags": tags, "geometry": geometry})
        data = {"elements": elements}
        print("OSM official map API returned", len(elements), "railway ways")
    except Exception as exc:
        print("Official OSM map API failed:", repr(exc))
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
