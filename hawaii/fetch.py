"""Download the law files listed in sources.json and verify each against the published sha256.

Usage: python3 fetch.py [--data DIR]
Needs: duckdb (only for cfr_slices, which are read remotely so the 1.4 GB CFR is never downloaded).
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (open-us-law hawaii fetch)"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    data = Path(sys.argv[sys.argv.index("--data") + 1]) if "--data" in sys.argv else HERE / "data"
    law = data / "law"
    law.mkdir(parents=True, exist_ok=True)
    src = json.loads((HERE / "sources.json").read_text())
    base, snap = src["base_url"], src["snapshot"]
    with urllib.request.urlopen(urllib.request.Request(f"{base}/index.json", headers=UA), timeout=60) as r:
        manifest = json.load(r)
    if manifest.get("version") != snap:
        print(f"note: newest snapshot is {manifest.get('version')}; sources.json pins {snap}")
    published = {f["file"]: f for f in manifest["files"]} if manifest.get("version") == snap else {}
    for entry in src["files"]:
        name = entry["file"]
        dest = law / name
        want = published.get(name, {}).get("sha256")
        if dest.exists() and (not want or sha256(dest) == want):
            print(f"ok      {name}")
            continue
        url = f"{base}/{snap}/{name}"
        print(f"fetch   {name}")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(dest, "wb") as f:
            for chunk in iter(lambda: r.read(1 << 20), b""):
                f.write(chunk)
        got = sha256(dest)
        if want and got != want:
            dest.unlink()
            sys.exit(f"checksum mismatch for {name}: expected {want}, got {got}")
        print(f"        sha256 {got}{' (verified)' if want else ' (no published hash for this snapshot)'}")
    if src.get("cfr_slices"):
        import duckdb
        con = duckdb.connect()
        con.sql("install httpfs; load httpfs")
        url = f"{base}/{snap}/us_federal_regulations.parquet"
        for sl in src["cfr_slices"]:
            dest = law / f"{sl['name']}.parquet"
            if dest.exists():
                print(f"ok      {dest.name}")
                continue
            print(f"slice   {dest.name}  ({sl['why']})")
            con.sql(f"copy (select * from '{url}' where {sl['where']}) to '{dest}' (format parquet)")
    print(f"data in {law}")


if __name__ == "__main__":
    main()
