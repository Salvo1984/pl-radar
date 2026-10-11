#!/usr/bin/env python3
"""Test di sola lettura dell'endpoint ViaggiaTreno, senza chiavi o dipendenze."""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

OUTPUT = pathlib.Path("data/viaggiatreno-test.json")
BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/autocompletaStazione/"
results = {}
for query in ("Palma", "Nola", "Sarno"):
    req = urllib.request.Request(BASE + urllib.parse.quote(query), headers={
        "User-Agent": "PLRadarResearch/0.1 (public station lookup test)",
        "Accept": "text/plain",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            text = response.read(16000).decode("utf-8", errors="replace")
            results[query] = {"ok": True, "status": response.status, "sample": text[:3000]}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        results[query] = {"ok": False, "error": str(exc)[:300]}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({
    "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "source": "ViaggiaTreno unofficial endpoint",
    "purpose": "Connectivity and station identification only; not level crossing state",
    "results": results,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(OUTPUT.read_text(encoding="utf-8")[:4000])
