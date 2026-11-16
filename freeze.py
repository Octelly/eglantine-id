#!/usr/bin/env python3
"""Freeze the app into out/. Fails loudly on any non-200."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import main

OUT = Path(__file__).parent / "out"


def freeze() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    client = TestClient(main.app)
    written = 0
    for url in main.urls():
        response = client.get(url)
        if response.status_code != 200:
            print(f"FAIL {url} -> {response.status_code} {response.text[:200]}", file=sys.stderr)
            return 1
        target = OUT / ("index.html" if url == "/" else url.lstrip("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        written += 1
    print(f"froze {written} files into {OUT}")
    return 0


def main_() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enrich", action="store_true", help="probe the binary caches and GitHub first")
    args = parser.parse_args()
    if args.enrich:
        import enrich
        print(f"enriched {enrich.enrich_all()} records")
    return freeze()


if __name__ == "__main__":
    raise SystemExit(main_())
