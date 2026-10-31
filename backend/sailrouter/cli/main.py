from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from sailrouter.service.project_paths import REPO_ROOT, ProjectPaths
from sailrouter.service.route_planner import RoutePlanner
from sailrouter.cli.route_file_writer import RouteFileWriter
from sailrouter.cli.route_summary_printer import RouteSummaryPrinter
from sailrouter.domain.position_parser import PositionParser
from sailrouter.polar.boat_options import BoatOptions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m sailrouter", description="VR routing advisor (GFS).")
    commands = parser.add_subparsers(dest="command", required=True)
    route = commands.add_parser("route", help="route one boat on the latest deterministic GFS run")
    route.add_argument("--race", default="route-du-rhum-2026", help="race id (file name in races/)")
    route.add_argument("--boat", default=None, help="boat id in the race file (default: the race default)")
    route.add_argument("--position", required=True, help="""e.g. "48°43'48\\"N 001°54'00\\"W" or "48.73, -1.9\"""")
    route.add_argument("--hours", type=float, default=120.0, help="routing horizon in hours (default 120)")
    route.add_argument("--start", default=None, help="UTC start, ISO 8601 (default: race start, or now if later)")
    route.add_argument("--next-mark", default=None, help="id of the next mark, if earlier marks are passed")
    route.add_argument("--options", default="all",
                       help='owned VR options: "all", "none" (Jib + Spi only) or a list of sails (LightJib, LightGnk, '
                            'Staysail, HeavyGnk, Code0), packs (light, heavy, reach) and foil, hull, pro_winch; '
                            'e.g. "foil" or "Code0,LightGnk,foil"')
    route.add_argument("--name", default=None, help="output file name in var/routes/ (no extension)")
    route.add_argument("--root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    position = PositionParser().parse(args.position)
    if position is None:
        print(f"Position not understood: {args.position!r}", file=sys.stderr)
        return 2
    start = _parse_start(args.start) if args.start else None
    paths = ProjectPaths(args.root)
    try:
        options = BoatOptions.from_owned(args.options)
        planner = RoutePlanner(paths, on_download=_print_download_progress)
        report = planner.plan(args.race, args.boat, position, args.hours, start, args.next_mark, options)
    except (ValueError, KeyError, RuntimeError, ConnectionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    RouteSummaryPrinter(sys.stdout).print(report)
    name = args.name or f"{report.race_id}-{report.boat_id}-{report.route.start:%Y%m%dT%H%M}"
    json_path, geojson_path = RouteFileWriter(paths.routes_dir).write(report, name)
    print(f"Wrote {json_path.relative_to(paths.root)} and {geojson_path.relative_to(paths.root)}")
    return 0


def _print_download_progress(done: int, total: int) -> None:
    print(f"\rDownloading GFS: {done}/{total} files", end="" if done < total else "\n", file=sys.stderr, flush=True)


def _parse_start(text: str) -> datetime:
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
