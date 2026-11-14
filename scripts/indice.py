#!/usr/bin/env python3
"""Crea el índice <id>.json de un mapa ya partido en trozos (se ejecuta dentro de out/)."""
import datetime, glob, json, os

mid = os.environ["ID"]
parts = sorted(glob.glob(f"{mid}.mbtiles.part*"))
index = {
    "id": mid,
    "name": os.environ["NOMBRE"],
    "date": datetime.date.today().isoformat(),
    "bytes": int(os.environ["BYTES"]),
    "bounds": [float(x) for x in os.environ["BOUNDS"].split(",")],
    "parts": [{"name": p, "bytes": os.path.getsize(p)} for p in parts],
}
json.dump(index, open(f"{mid}.json", "w"), ensure_ascii=False)
print(json.dumps(index, ensure_ascii=False, indent=1))
