from __future__ import annotations

from pathlib import Path

from campnet.models import ProviderResult, Survey, SurveyMetadata, utc_now
from campnet.radio import NetworkInfo, RadioSnapshot, radio_snapshot_to_dict
from campnet.storage import load_survey, save_survey


def test_save_and_load_survey(tmp_path: Path) -> None:
    survey = Survey(timestamp=utc_now(), metadata=SurveyMetadata(notes="hello"))
    path = tmp_path / "nested" / "survey.json"

    assert save_survey(survey, path) == path
    assert load_survey(path) == survey
    assert not path.with_suffix(".json.tmp").exists()


def test_loading_legacy_schema_one_normalizes_radio_without_rewriting(tmp_path: Path) -> None:
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(
            ProviderResult(
                provider="at",
                collected_at=utc_now(),
                raw_responses={
                    "AT+QNWINFO#1": (
                        '+QNWINFO: "FDD LTE","310410","LTE BAND 2",1125\nOK\n'
                    )
                },
            ),
        ),
    )
    path = tmp_path / "survey.json"
    save_survey(survey, path)
    original = path.read_bytes()

    loaded = load_survey(path)

    assert "radio" in loaded.provider_results[0].data
    assert path.read_bytes() == original


def test_loading_affected_multi_sim_survey_recovers_passive_carrier_data(
    tmp_path: Path,
) -> None:
    active_radio = radio_snapshot_to_dict(
        RadioSnapshot(
            networks=(NetworkInfo("FDD LTE", "310410", "LTE BAND 2", 1125),)
        )
    )
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(
            ProviderResult(
                provider="at",
                collected_at=utc_now(),
                data={"radio": active_radio, "multi_sim": {"segments": []}},
                raw_responses={
                    "AT+QSCAN=1#1": (
                        '+QSCAN: "LTE",311,480,5230,207,-94,-13,34,113\nOK\n'
                    )
                },
            ),
        ),
    )
    path = tmp_path / "affected-multi-sim.json"
    save_survey(survey, path)
    original = path.read_bytes()

    loaded = load_survey(path)
    radio = loaded.provider_results[0].data["radio"]

    assert isinstance(radio, dict)
    assert isinstance(radio["visible_cells"], list)
    assert len(radio["visible_cells"]) == 1
    assert path.read_bytes() == original
