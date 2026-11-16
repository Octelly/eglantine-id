"""Enrichment: is the artefact really in a cache, and who authored the commit?

Both probes are best-effort. A failed lookup leaves the field as None rather
than writing a guess.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from store import DATA, load_all

CACHES = ("https://octelly.cachix.org", "https://eglantine.cachix.org")
API = "https://api.github.com"
UA = {"User-Agent": "eglantine-id/1 (+https://github.com/Octelly/eglantine-id)"}


def _get(url: str, timeout: float = 10.0) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def narinfo(store_hash: str) -> tuple[bool | None, str | None]:
    """True/False = probed; None = could not reach any cache."""
    unreachable = True
    for cache in CACHES:
        try:
            body = _get(f"{cache}/{store_hash}.narinfo").decode()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                unreachable = False
                continue
            continue
        except Exception:
            continue
        unreachable = False
        fields = dict(line.split(": ", 1) for line in body.splitlines() if ": " in line)
        return True, fields.get("NarHash")
    return (None if unreachable else False), None


def commit_info(repo: str, rev: str) -> tuple[datetime | None, str | None]:
    try:
        payload = json.loads(_get(f"{API}/repos/{repo}/commits/{rev}"))
    except Exception:
        return None, None
    commit = payload.get("commit") or {}
    date = (commit.get("committer") or {}).get("date")
    author = (commit.get("author") or {}).get("name")
    parsed = None
    if date:
        try:
            parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
    return parsed, author


def enrich_all() -> int:
    changed = 0
    for record in load_all():
        cached, nar_hash = narinfo(record.store_hash)
        commit_date, author = commit_info(record.repo, record.rev)
        record.cached = cached
        record.narHash = nar_hash or record.narHash
        record.commitDate = commit_date or record.commitDate
        record.author = author or record.author
        record.enrichedAt = datetime.now(timezone.utc)
        path = DATA / record.system / f"{record.store_hash}.json"
        path.write_text(json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n")
        changed += 1
        print(f"enriched {record.store_hash}: cached={cached} narHash={'yes' if record.narHash else 'no'} author={author}")
    return changed
