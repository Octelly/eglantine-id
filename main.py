"""The read side: a FastAPI app that freeze.py turns into static files.

Production is GitHub Pages; nothing here serves live traffic.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from models import DbIndex
from store import build_index, load_all

app = FastAPI(title="Eglantine build identity", version="1")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
def page(request: Request) -> HTMLResponse:
    records = sorted(load_all(), key=lambda r: (r.commitDate or r.registeredAt), reverse=True)
    return templates.TemplateResponse(request, "index.html", {"records": records})


@app.get("/healthz.json")
def healthz() -> dict:
    return {"ok": True, "builds": len(load_all())}


@app.get("/db/index.json", response_model=DbIndex)
def index() -> DbIndex:
    return build_index(load_all())


@app.get("/db/build/{store_hash}.json")
def build(store_hash: str) -> JSONResponse:
    for record in load_all():
        if record.store_hash == store_hash:
            return JSONResponse(record.model_dump(mode="json"))
    raise HTTPException(status_code=404, detail="unknown build")


@app.get("/db/rev/{rev}.json")
def rev(rev: str) -> JSONResponse:
    hits = [r.model_dump(mode="json") for r in load_all() if r.rev == rev]
    if not hits:
        raise HTTPException(status_code=404, detail="unknown rev")
    return JSONResponse({"rev": rev, "builds": hits})


def urls() -> list[str]:
    """Every URL the freezer materialises."""
    records = load_all()
    paths = ["/", "/healthz.json", "/db/index.json"]
    paths += [f"/db/build/{r.store_hash}.json" for r in records]
    paths += [f"/db/rev/{rev}.json" for rev in sorted({r.rev for r in records})]
    return paths
