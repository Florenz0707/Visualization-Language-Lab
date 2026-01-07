from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_provenance(
    out_path: str | Path,
    *,
    generated_by: str,
    source_files: Iterable[str] | None = None,
    processing_steps: Iterable[str] | None = None,
    confidence_note: Optional[str] = None,
    extra: Optional[dict] = None,
):
    """Write a small provenance JSON file alongside generated data.

    Args:
        out_path: path to write provenance JSON (file will be created/overwritten)
        generated_by: script or tool name
        source_files: list of source file paths or URLs
        processing_steps: short descriptions of processing steps
        confidence_note: optional human note about confidence
        extra: optional dict merged into metadata
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "generated_at": _utc_now_iso(),
        "generated_by": generated_by,
        "source_files": list(source_files or []),
        "processing_steps": list(processing_steps or []),
    }
    if confidence_note:
        metadata["confidence_note"] = confidence_note
    if extra:
        metadata.update(extra)

    with open(p, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

    return p
