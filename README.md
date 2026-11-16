# eglantine-id

Build identity database for [Eglantine](https://github.com/Octelly/Eglantine).

A Nix store path is content-addressed, so a binary can be cached and still be
labelled correctly — but only if the label lives somewhere other than the
derivation. This repo is that somewhere: CI reports what it built, this repo
records it, and the emulator asks at startup.

## How a build gets registered

1. A CI leg that successfully built its derivation writes
   `inbox/<system>-<store-hash>.json` and pushes (SSH deploy key, write access).
2. This repo's workflow validates the payload, moves it to
   `data/builds/<system>/<store-hash>.json` **once**, enriches it against the
   binary caches and the GitHub API, freezes the site and deploys to Pages.

Nothing is ever rewritten for a given store path: a build's identity is fixed at
the moment it is registered.

## The API (static files, served by Pages)

| path | meaning |
|---|---|
| `/db/index.json` | every build, one fetch, ETag-cacheable |
| `/db/build/<store-hash>.json` | one record, `404` when unknown |
| `/db/rev/<sha>.json` | every build of one commit |
| `/healthz.json` | liveness + count |

`/` is a human-readable list.

## Payload

```json
{
  "storePath": "/nix/store/<hash>-eglantine-<version>",
  "identity": "Octelly/Eglantine/nx2-experimental - 2026-11-14_18-09 (6963d05)",
  "rev": "6963d05…",
  "ref": "nx2-experimental",
  "system": "x86_64-linux",
  "pgo": false,
  "march": null,
  "repo": "Octelly/Eglantine",
  "run": "43624997465",
  "workflow": "build-nix.yml"
}
```

## Local use

```console
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --reload        # preview with live data
python3 freeze.py --enrich                  # what CI does
```
