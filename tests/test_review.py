from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from campnet.models import Survey, SurveyMetadata
from campnet.review import discover_surveys, review_surveys
from campnet.storage import save_survey


def _save(
    directory: Path,
    filename: str,
    *,
    location: str | None,
    site: str | None,
    day: int,
) -> None:
    save_survey(
        Survey(
            timestamp=datetime(2026, 8, day, 12, 0, tzinfo=UTC),
            metadata=SurveyMetadata(campground=location, site=site),
        ),
        directory / filename,
    )


def test_discover_surveys_skips_malformed_files(tmp_path: Path) -> None:
    _save(tmp_path, "valid.json", location="Park", site="1", day=1)
    (tmp_path / "broken.json").write_text("not JSON", encoding="utf-8")

    records, errors = discover_surveys(tmp_path)

    assert [record.path.name for record in records] == ["valid.json"]
    assert len(errors) == 1
    assert errors[0].startswith("Skipped broken.json:")


def test_review_navigates_location_site_and_newest_scan(tmp_path: Path) -> None:
    _save(tmp_path, "older.json", location="Petoskey State Park", site="30", day=10)
    _save(tmp_path, "newer.json", location="Petoskey State Park", site="30", day=12)
    _save(tmp_path, "other.json", location="Other Park", site="2", day=11)
    responses = iter(("2", "1", "1", "", "0", "0", "0"))
    output: list[str] = []

    result = review_surveys(
        tmp_path,
        input_function=lambda prompt: next(responses),
        output_function=output.append,
    )

    assert result == 0
    text = "\n".join(output)
    assert text.index("2026-08-12 12:00:00 UTC - newer.json") < text.index(
        "2026-08-10 12:00:00 UTC - older.json"
    )
    assert "Location:    Petoskey State Park, site 30" in text


def test_review_reports_empty_directory(tmp_path: Path) -> None:
    output: list[str] = []

    assert review_surveys(tmp_path, output_function=output.append) == 1
    assert "No readable surveys found" in output[-1]
