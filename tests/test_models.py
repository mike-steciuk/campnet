from __future__ import annotations

from campnet.models import ProviderResult, Survey, SurveyMetadata, utc_now


def test_survey_round_trip() -> None:
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(campground="Petoskey State Park", site="212"),
        provider_results=(
            ProviderResult(
                provider="fixture",
                collected_at=utc_now(),
                data={"rsrp": -95, "bands": [2, 14]},
                raw_responses={"AT+QENG": "+QENG: servingcell\nOK"},
            ),
        ),
    )

    restored = Survey.from_dict(survey.to_dict())

    assert restored == survey


def test_unknown_schema_is_rejected() -> None:
    survey = Survey(timestamp=utc_now(), metadata=SurveyMetadata()).to_dict()
    survey["schema_version"] = 99

    try:
        Survey.from_dict(survey)
    except ValueError as error:
        assert "unsupported survey schema" in str(error)
    else:
        raise AssertionError("unknown schema version was accepted")


def test_new_surveys_receive_unique_ids() -> None:
    first = Survey(timestamp=utc_now(), metadata=SurveyMetadata())
    second = Survey(timestamp=utc_now(), metadata=SurveyMetadata())

    assert first.survey_id != second.survey_id


def test_legacy_survey_without_id_gets_stable_derived_id() -> None:
    document = Survey(timestamp=utc_now(), metadata=SurveyMetadata()).to_dict()
    del document["survey_id"]

    assert Survey.from_dict(document).survey_id == Survey.from_dict(document).survey_id
