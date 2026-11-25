"""Zertifikats-Material aufloesen: Pfad im Add-on oder inline-PEM aus den Optionen."""
from __future__ import annotations

from pathlib import Path


def resolve_material(value: str, fallback: str, data_dir: Path, filename: str) -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    if "-----BEGIN" in value:
        target = data_dir / "generated"
        target.mkdir(parents=True, exist_ok=True)
        out = target / filename
        out.write_text(value + "\n")
        return str(out)
    return value
