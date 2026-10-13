#!/usr/bin/env python3
"""Pubblica soltanto monitor di stazione ViaggiaTreno. Non predice passaggi a livello."""
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request
import sys
from zoneinfo import ZoneInfo

BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"
STATIONS = {"Palma S. Gennaro": "S09701", "Nola": "S09700", "Sarno": "S09702"}
now = dt.datetime.now(ZoneInfo("Europe/Rome"))
# L'endpoint usa una stringa data locale. Mantenere il formato usato nel test riuscito.
offset = now.strftime("%z")
offset_label = "GMT" + offset[:3] + ":" + offset[3:]
date = now.strftime("%a %b %d %Y %H:%M:%S ") + offset_label + " (Central European Summer Time)"
result = {"updated_at": now.isoformat(), "source": "ViaggiaTreno (endpoint non ufficiale)", "disclaimer": "Orari di stazione, NON stato sbarre o previsione transiti; treni merci non garantiti", "stations": []}
successful = 0
for name, code in STATIONS.items():
    entry = {"name": name, "code": code, "departures": [], "arrivals": [], "errors": []}
    for endpoint, key in (("partenze", "departures"), ("arrivi", "arrivals")):
        url = BASE + endpoint + "/" + code + "/" + urllib.parse.quote(date, safe="")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read(300000))
            if not isinstance(data, list):
                raise ValueError("Unexpected response shape")
            successful += 1
            for train in data[:40]:
                if not isinstance(train, dict):
                    continue
                time_key = "compOrarioPartenza" if key == "departures" else "compOrarioArrivo"
                fallback = "orarioPartenza" if key == "departures" else "orarioArrivo"
                clock = train.get(time_key)
                if not isinstance(clock, str) or not clock.strip():
                    timestamp = train.get(fallback)
                    if isinstance(timestamp, (int, float)):
                        clock = dt.datetime.fromtimestamp(timestamp / 1000, ZoneInfo("Europe/Rome")).strftime("%H:%M")
                    else:
                        clock = None
                entry[key].append({
                    "train": str(train.get("compNumeroTreno") or train.get("numeroTreno") or "")[:40],
                    "time": clock,
                    "destination": str(train.get("destinazione") or "")[:100] if key == "departures" else "",
                    "origin": str(train.get("origine") or "")[:100] if key == "arrivals" else "",
                    "delay_minutes": train.get("ritardo") if isinstance(train.get("ritardo"), int) else None,
                    "not_departed": bool(train.get("nonPartito")),
                })
        except Exception as exc:
            entry["errors"].append(endpoint + ": " + str(exc)[:160])
    result["stations"].append(entry)
    print(name + ": " + ("; ".join(entry["errors"]) if entry["errors"] else "both endpoints OK"), file=sys.stderr, flush=True)
# Non sovrascrivere dati validi con un file vuoto se l'endpoint è totalmente indisponibile.
if successful == 0:
    raise SystemExit("No ViaggiaTreno endpoint succeeded; previous published data unchanged")
out = pathlib.Path("data/viaggiatreno-stations.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Successful monitor requests:", successful, "/ 6")
for entry in result["stations"]:
    print(entry["name"], len(entry["departures"]), "departures,", len(entry["arrivals"]), "arrivals,", len(entry["errors"]), "errors")
