"""Interactive console browser for locally stored CampNet surveys."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

from campnet.models import Survey
from campnet.report import format_survey
from campnet.storage import load_survey

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]

UNSPECIFIED_LOCATION = "Unspecified location"
UNSPECIFIED_SITE = "Unspecified site"


@dataclass(frozen=True, slots=True)
class SurveyRecord:
    path: Path
    survey: Survey

    @property
    def location(self) -> str:
        return self.survey.metadata.campground or UNSPECIFIED_LOCATION

    @property
    def site(self) -> str:
        return self.survey.metadata.site or UNSPECIFIED_SITE


def discover_surveys(directory: Path) -> tuple[tuple[SurveyRecord, ...], tuple[str, ...]]:
    records: list[SurveyRecord] = []
    errors: list[str] = []
    if not directory.is_dir():
        return (), (f"Survey directory not found: {directory}",)
    for path in sorted(directory.rglob("*.json")):
        try:
            records.append(SurveyRecord(path=path, survey=load_survey(path)))
        except (OSError, ValueError) as error:
            errors.append(f"Skipped {path.name}: {type(error).__name__}: {error}")
    return tuple(records), tuple(errors)


def review_surveys(
    directory: Path = Path("surveys"),
    *,
    input_function: InputFunction = input,
    output_function: OutputFunction = print,
) -> int:
    records, errors = discover_surveys(directory)
    output_function("CampNet Survey Review")
    output_function("=====================")
    for error in errors:
        output_function(f"Warning: {error}")
    if not records:
        output_function(f"No readable surveys found beneath {directory}.")
        return 1

    while True:
        locations = sorted({record.location for record in records}, key=str.casefold)
        location = _choose(
            "Locations",
            locations,
            exit_label="Quit",
            input_function=input_function,
            output_function=output_function,
        )
        if location is None:
            return 0

        location_records = tuple(record for record in records if record.location == location)
        while True:
            sites = sorted({record.site for record in location_records}, key=_site_sort_key)
            site = _choose(
                f"Sites at {location}",
                sites,
                exit_label="Back to locations",
                input_function=input_function,
                output_function=output_function,
            )
            if site is None:
                break

            site_records = sorted(
                (record for record in location_records if record.site == site),
                key=lambda record: record.survey.timestamp,
                reverse=True,
            )
            while True:
                labels = [_scan_label(record, directory) for record in site_records]
                selected_label = _choose(
                    f"Scans for {location}, site {site}",
                    labels,
                    exit_label="Back to sites",
                    input_function=input_function,
                    output_function=output_function,
                )
                if selected_label is None:
                    break
                selected = site_records[labels.index(selected_label)]
                output_function("")
                output_function(format_survey(selected.survey))
                output_function("")
                try:
                    input_function("Press Enter to return to this site's scans...")
                except (EOFError, KeyboardInterrupt):
                    return 0


def _choose(
    heading: str,
    choices: list[str],
    *,
    exit_label: str,
    input_function: InputFunction,
    output_function: OutputFunction,
) -> str | None:
    while True:
        output_function("")
        output_function(heading)
        output_function("-" * len(heading))
        for number, choice in enumerate(choices, start=1):
            output_function(f"{number}. {choice}")
        output_function(f"0. {exit_label}")
        try:
            response = input_function("Select an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if response.isdecimal():
            selection = int(response)
            if selection == 0:
                return None
            if 1 <= selection <= len(choices):
                return choices[selection - 1]
        output_function(f"Please enter a number from 0 to {len(choices)}.")


def _scan_label(record: SurveyRecord, root: Path) -> str:
    timestamp = record.survey.timestamp.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        filename = record.path.relative_to(root)
    except ValueError:
        filename = record.path
    return f"{timestamp} - {filename}"


def _site_sort_key(value: str) -> tuple[int, int | str]:
    if value.isdecimal():
        return (0, int(value))
    return (1, value.casefold())
