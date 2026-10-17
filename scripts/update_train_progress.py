#!/usr/bin/env python3
"""Diagnostic-only ViaggiaTreno andamentoTreno collector. Never predicts barrier status."""
import datetime as dt
import json
import pathlib
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"
now = dt.datetime.now(ZoneInfo("Europe/Rome"))
stations = json.loads(pathlib.Path("data/viaggiatreno-stations.json").read_text(encoding="utf-8"))
trains = {}
for station in stations.get("stations", []):
    for direction in ("departures", "arrivals"):
        for entry in station.get(direction, []):
            match = re.search(r"\b(\d{3,6})\b", str(entry.get("train", "")))
            if match:
                trains[match.group(1)] = str(entry.get("train", ""))[:50]
out = {
    "updated_at": now.isoformat(),
    "source": "ViaggiaTreno / andamentoTreno (API non ufficiale)",
    "diagnostic_only": True,
    "disclaimer": "Dati ferroviari sperimentali. Non indicano posizione GPS, passaggio al PL o stato delle sbarre.",
    "trains": [],
}
for number, label in list(trains.items())[:15]:
    record = {"train": label, "number": number, "ok": False, "stops": [], "error": None}
    try:
        # endpoint andamentoTreno/<origine>/<numero>/<dataPartenza>; 0 è il valore
        # di ricerca non associato a un identificativo di origine specifico.
        url = BASE + "andamentoTreno/0/" + urllib.parse.quote(number) + "/0"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read(400000))
        if not isinstance(payload, dict):
            raise ValueError("Risposta non valida")
        stops = payload.get("fermate")
        if not isinstance(stops, list):
            raise ValueError("Elenco fermate non presente")
        record["ok"] = True
        record["stops"] = [
            {
                "station": str(s.get("stazione") or "")[:90],
                "station_id": str(s.get("id") or "")[:30],
                "scheduled_arrival": s.get("arrivo_teorico"),
                "actual_arrival": s.get("arrivoReale"),
                "scheduled_departure": s.get("partenza_teorica"),
                "actual_departure": s.get("partenzaReale"),
            }
            for s in stops[:60] if isinstance(s, dict)
        ]
        record["delay_minutes"] = payload.get("ritardo") if isinstance(payload.get("ritardo"), int) else None
    except Exception as exc:
        record["error"] = str(exc)[:180]
    out["trains"].append(record)
dest = pathlib.Path("data/train-progress-diagnostic.json")
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("AndamentoTreno diagnostic:", len(out["trains"]), "trains,", sum(t["ok"] for t in out["trains"]), "valid responses")
