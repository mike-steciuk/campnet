from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from campnet.models import ProviderResult, Survey, SurveyMetadata, utc_now
from campnet.report import format_survey, rsrp_quality


def test_human_report_includes_radio_interpretation() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "quectel_basic.json"
    fixture = cast(dict[str, str], json.loads(fixture_path.read_text(encoding="utf-8")))
    raw = {f"{command}#1": response for command, response in fixture.items()}
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(campground="Test Camp", site="12"),
        provider_results=(
            ProviderResult(provider="at", collected_at=utc_now(), raw_responses=raw),
        ),
    )

    report = format_survey(survey)

    assert "Location:    Test Camp, site 12" in report
    assert "Quectel RM520N-GL" in report
    assert "AT&T: FDD LTE, LTE BAND 2" in report
    assert "RSRP: -108 dBm (Weak)" in report
    assert "active non-standalone 5G" in report


def test_report_summarizes_visible_carriers() -> None:
    raw = {
        "AT+COPS=?#1": '+COPS: (1,"Verizon","Verizon","311480",7)\nOK\n',
        "AT+QSCAN=1#1": '+QSCAN: "LTE",311,480,5230,207,-94,-13,34,113\nOK\n',
    }
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(
            ProviderResult(provider="at", collected_at=utc_now(), raw_responses=raw),
        ),
    )

    report = format_survey(survey)

    assert "Operators: Verizon (available)" in report
    assert "Verizon: 1 cells; best LTE BAND 13, RSRP: -94 dBm (Fair)" in report


def test_report_includes_restorable_modem_preferences() -> None:
    raw = {
        'AT+QNWPREFCFG="mode_pref"#1': '+QNWPREFCFG: "mode_pref",AUTO\nOK\n',
        'AT+QNWPREFCFG="lte_band"#1': '+QNWPREFCFG: "lte_band",2:5:12:14:66\nOK\n',
    }
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(
            ProviderResult(provider="at", collected_at=utc_now(), raw_responses=raw),
        ),
    )

    report = format_survey(survey)

    assert "mode_pref: AUTO" in report
    assert "lte_band: 2:5:12:14:66" in report


def test_report_includes_speedtest_result() -> None:
    survey = Survey(
        timestamp=utc_now(),
        metadata=SurveyMetadata(),
        provider_results=(
            ProviderResult(
                provider="speedtest",
                collected_at=utc_now(),
                data={
                    "download_mbps": 47.25,
                    "upload_mbps": 8.5,
                    "latency_ms": 31.2,
                    "jitter_ms": 2.1,
                    "packet_loss_percent": 0.0,
                    "isp": "Example ISP",
                    "execution_scope": "collector_host",
                },
            ),
        ),
    )

    report = format_survey(survey)

    assert f"Survey ID:   {survey.survey_id}" in report
    assert "Download:   47.250 Mbps" in report
    assert "Upload:     8.500 Mbps" in report
    assert "ISP:         Example ISP" in report
    assert "Measured on: Collector computer" in report


def test_rsrp_quality_boundaries() -> None:
    assert rsrp_quality(-80) == "Excellent"
    assert rsrp_quality(-90) == "Good"
    assert rsrp_quality(-100) == "Fair"
    assert rsrp_quality(-110) == "Weak"
    assert rsrp_quality(-111) == "Very weak"
