#!/usr/bin/env python3
"""Move validated payloads from inbox/ into data/builds/. Rejects are fatal."""
from __future__ import annotations

import json
import sys

from models import BuildPayload
from store import INBOX, write_record


def main() -> int:
    created = duplicate = rejected = 0
    for path in sorted(INBOX.glob("*.json")):
        try:
            payload = BuildPayload(**json.loads(path.read_text()))
        except Exception as exc:  # validation or JSON error
            print(f"REJECT {path.name}: {exc}", file=sys.stderr)
            rejected += 1
            continue
        target, is_new = write_record(payload)
        path.unlink()
        print(f"{'new  ' if is_new else 'dup  '} {target.relative_to(target.parents[2])}")
        created += int(is_new)
        duplicate += int(not is_new)
    print(f"ingest: {created} new, {duplicate} duplicate, {rejected} rejected")
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
