from __future__ import annotations

from pathlib import Path

from campnet.models import Survey, SurveyMetadata, utc_now
from campnet.storage import load_survey, save_survey


def test_save_and_load_survey(tmp_path: Path) -> None:
    survey = Survey(timestamp=utc_now(), metadata=SurveyMetadata(notes="hello"))
    path = tmp_path / "nested" / "survey.json"

    assert save_survey(survey, path) == path
    assert load_survey(path) == survey
    assert not path.with_suffix(".json.tmp").exists()
