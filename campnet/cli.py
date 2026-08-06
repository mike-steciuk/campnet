"""Command-line interface for collecting and reading surveys."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from campnet.at import ATClient
from campnet.collector import SurveyCollector
from campnet.models import Survey, SurveyMetadata
from campnet.providers import (
    CONTINUOUS_COMMANDS,
    ONE_OFF_COMMANDS,
    ATProvider,
    DataProvider,
    GNSSProvider,
    SystemProvider,
)
from campnet.report import format_survey
from campnet.storage import load_survey, save_survey
from campnet.transports import ReplayTransport, SSHATTransport


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="campnet", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    collect = commands.add_parser("collect", help="collect and save a survey")
    collect.add_argument("--campground")
    collect.add_argument("--site")
    collect.add_argument("--notes")
    collect.add_argument("--router-placement")
    collect.add_argument("--antenna-configuration")
    collect.add_argument("--output", type=Path)
    collect.add_argument(
        "--at-fixture",
        type=Path,
        help="replay captured AT responses instead of contacting hardware",
    )
    collect.add_argument("--ssh-host", help="collect live AT data through a GL.iNet router")
    collect.add_argument("--ssh-user", default="root")
    collect.add_argument("--modem-bus", default="1-1.2")
    collect.add_argument(
        "--profile",
        choices=("one-off", "continuous"),
        default="one-off",
        help="one-off includes slow scans; continuous keeps collection lightweight",
    )
    collect.add_argument(
        "--no-gps",
        action="store_true",
        help="skip GNSS collection during a one-off survey",
    )

    show = commands.add_parser("show", help="display a saved survey")
    show.add_argument("path", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "collect":
        if args.at_fixture and args.ssh_host:
            raise SystemExit("--at-fixture and --ssh-host cannot be used together")
        metadata = SurveyMetadata(
            campground=args.campground,
            site=args.site,
            notes=args.notes,
            router_placement=args.router_placement,
            antenna_configuration=args.antenna_configuration,
        )
        providers: list[DataProvider] = [SystemProvider()]
        commands = ONE_OFF_COMMANDS if args.profile == "one-off" else CONTINUOUS_COMMANDS
        if args.at_fixture:
            fixture_transport = ReplayTransport.from_json(args.at_fixture)
            providers.append(ATProvider(ATClient(fixture_transport), commands=commands))
        if args.ssh_host:
            ssh_transport = SSHATTransport(
                args.ssh_host,
                user=args.ssh_user,
                modem_bus=args.modem_bus,
            )
            client = ATClient(ssh_transport)
            providers.append(ATProvider(client, commands=commands))
            if not args.no_gps:
                providers.append(GNSSProvider(client, enable_if_needed=args.profile == "one-off"))
        print(f"Collecting {args.profile} survey; this may take several minutes...")
        survey = SurveyCollector(providers).collect(metadata)
        output = args.output or _default_output(survey)
        save_survey(survey, output)
        print(format_survey(survey))
        print(f"Saved: {output}")
        return 0
    if args.command == "show":
        print(format_survey(load_survey(args.path)))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


def _default_output(survey: Survey) -> Path:
    timestamp = survey.timestamp.strftime("%Y%m%dT%H%M%SZ")
    return Path("surveys") / f"survey-{timestamp}.json"


if __name__ == "__main__":
    raise SystemExit(main())
