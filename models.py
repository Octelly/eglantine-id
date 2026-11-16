"""Models for the Eglantine build-identity database.

A CI leg drops a BuildPayload into inbox/; ingest.py validates it and writes a
BuildRecord to data/builds/<system>/<store-hash>.json, one file per build.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

STORE_PATH_RE = re.compile(r"^/nix/store/[a-z0-9]{32}-[A-Za-z0-9+._?=-]+$")
STORE_HASH_RE = re.compile(r"^[a-z0-9]{32}$")
REV_RE = re.compile(r"^[0-9a-f]{7,40}$")
SYSTEMS = {"x86_64-linux", "aarch64-linux", "x86_64-darwin", "aarch64-darwin"}
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class BuildPayload(BaseModel):
    storePath: str
    identity: str = Field(min_length=3, max_length=200)
    rev: str
    ref: str = Field(min_length=1, max_length=200)
    system: str
    pgo: bool = False
    march: str | None = None
    repo: str = Field(min_length=3, max_length=140)
    run: str = Field(min_length=1, max_length=40)
    workflow: str = Field(min_length=1, max_length=120)

    @field_validator("storePath")
    @classmethod
    def _store_path(cls, v: str) -> str:
        if not STORE_PATH_RE.match(v):
            raise ValueError("not a /nix/store path")
        return v

    @field_validator("rev")
    @classmethod
    def _rev(cls, v: str) -> str:
        if not REV_RE.match(v):
            raise ValueError("rev must be 7-40 lowercase hex characters")
        return v

    @field_validator("system")
    @classmethod
    def _system(cls, v: str) -> str:
        if v not in SYSTEMS:
            raise ValueError(f"unknown system {v!r}")
        return v

    @field_validator("identity", "ref", "repo", "march")
    @classmethod
    def _no_control(cls, v):
        if isinstance(v, str) and CONTROL_RE.search(v):
            raise ValueError("control characters are not allowed")
        return v

    @property
    def store_hash(self) -> str:
        return self.storePath.rsplit("/", 1)[-1].split("-", 1)[0]

    @property
    def store_name(self) -> str:
        return self.storePath.rsplit("/", 1)[-1].split("-", 1)[1]


class BuildRecord(BuildPayload):
    registeredAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cached: bool | None = None
    narHash: str | None = None
    commitDate: datetime | None = None
    author: str | None = None
    enrichedAt: datetime | None = None


class IndexEntry(BaseModel):
    identity: str
    rev: str
    ref: str
    system: str
    pgo: bool
    march: str | None = None
    run: str
    cached: bool | None = None


class DbIndex(BaseModel):
    version: int = 1
    generated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    builds: dict[str, IndexEntry]
    revs: dict[str, list[str]]
