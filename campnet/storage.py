"""JSON persistence for canonical surveys."""

from __future__ import annotations

import json
from pathlib import Path

from campnet.models import JsonValue, Survey


def save_survey(survey: Survey, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(survey.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def load_survey(path: Path) -> Survey:
    value: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("survey document must contain a JSON object")
    return Survey.from_dict(value)
