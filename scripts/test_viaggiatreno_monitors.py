#!/usr/bin/env python3
"""Test manuale dei monitor arrivi/partenze ViaggiaTreno; nessuna previsione barriere."""
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.request
import urllib.parse

BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"
STATIONS = {"Palma S. Gennaro": "S09701", "Nola": "S09700", "Sarno": "S09702"}
date = dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).strftime("%a %b %d %Y %H:%M:%S GMT+0200 (Central European Summer Time)")
out = {}
for name, station in STATIONS.items():
    out[name] = {}
    for kind in ("partenze", "arrivi"):
        url = BASE + kind + "/" + station + "/" + urllib.parse.quote(date, safe="")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(100000).decode("utf-8", "replace")
                try:
                    parsed = json.loads(raw)
                    out[name][kind] = {"ok": True, "http_status": response.status, "count": len(parsed) if isinstance(parsed,list) else None, "sample": parsed[:2] if isinstance(parsed,list) else parsed}
                except json.JSONDecodeError:
                    out[name][kind] = {"ok": False, "http_status": response.status, "error": "non-JSON response", "sample": raw[:400]}
        except Exception as e:
            out[name][kind] = {"ok": False, "error": str(e)[:350]}
path = pathlib.Path("data/viaggiatreno-monitor-test.json")
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps({"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"warning":"Station data only, not crossing/barrier status","results":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
for name, results in out.items():
    print(name, {k:{"ok":v["ok"],"count":v.get("count"),"error":v.get("error")} for k,v in results.items()})
