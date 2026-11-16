"""On-disk store: one JSON file per build, written once."""
from __future__ import annotations

import json
from pathlib import Path

from models import BuildPayload, BuildRecord, DbIndex, IndexEntry

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "builds"
INBOX = ROOT / "inbox"


def record_path(payload: BuildPayload) -> Path:
    return DATA / payload.system / f"{payload.store_hash}.json"


def write_record(payload: BuildPayload) -> tuple[Path, bool]:
    path = record_path(payload)
    if path.exists():
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    record = BuildRecord(**payload.model_dump())
    path.write_text(json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n")
    return path, True


def load_all() -> list[BuildRecord]:
    return [BuildRecord(**json.loads(p.read_text())) for p in sorted(DATA.glob("*/*.json"))]


def build_index(records: list[BuildRecord]) -> DbIndex:
    builds: dict[str, IndexEntry] = {}
    revs: dict[str, list[str]] = {}
    for r in records:
        builds[r.storePath] = IndexEntry(
            identity=r.identity, rev=r.rev, ref=r.ref, system=r.system,
            pgo=r.pgo, march=r.march, run=r.run, cached=r.cached,
        )
        revs.setdefault(r.rev, []).append(r.storePath)
    return DbIndex(builds=builds, revs=revs)
