from __future__ import annotations

from typing import TextIO

from sailrouter.cli.position_formatter import PositionFormatter
from sailrouter.cli.route_report import RouteReport

HORIZONS_H = (4, 8, 12, 16, 24, 48)


class RouteSummaryPrinter:
    """Prints a short, human-readable summary of a `RouteReport` (route plan at the usual horizons)."""

    def __init__(self, out: TextIO) -> None:
        self._out = out
        self._positions = PositionFormatter()

    def print(self, report: RouteReport) -> None:
        route = report.route
        write = lambda text="": print(text, file=self._out)  # noqa: E731
        write(f"{report.race_name} — {report.boat_id}")
        write(f"From {self._positions.format(report.position.lat_deg, report.position.lon_deg)}, "
              f"start {route.start:%Y-%m-%d %H:%M} UTC, {report.step_count} steps")
        write(f"Weather: GFS 0.25° run {report.weather_run.cycle:%Y-%m-%d %H}Z "
              f"(next expected ≈ {report.next_run_expected:%Y-%m-%d %H:%M} UTC)")
        write()
        write(f"{'':>5}  {'time UTC':<11}  {'position':<25}  {'hdg':>4}  {'TWA':>5}  {'TWS':>5}  "
              f"{'sail':<9}  {'speed':>5}")
        for hours in (0, *HORIZONS_H):
            if route.covers(hours):
                write(self._row(hours, route.point_at(hours)))
        write()
        for k, leg in enumerate(report.progress.legs[:route.points[-1].marks_passed]):
            passed_at = next(p.time for p in route.points if p.marks_passed > k)
            hours = (passed_at - route.start).total_seconds() / 3600
            write(f"Passed {leg.mark_id} at +{hours:.0f} h")
        state = "finished" if route.finished else f"{route.distance_to_go_nm:.0f} nm to go"
        write(f"At {route.end:%Y-%m-%d %H:%M} UTC: {state}")
        timings = ", ".join(f"{name} {seconds:.1f} s" for name, seconds in report.timings_s.items())
        write(f"Compute time: {timings}")

    def _row(self, hours: float, point) -> str:
        position = self._positions.format(point.lat_deg, point.lon_deg)
        if point.heading_deg is None:
            return f"{'+' + str(hours) + ' h':>5}  {point.time:%d %H:%M}     {position:<25}"
        return (f"{'+' + str(hours) + ' h':>5}  {point.time:%d %H:%M}     {position:<25}  "
                f"{point.heading_deg:4.0f}  {point.twa_deg:+5.0f}  {point.tws_kn:5.1f}  "
                f"{point.sail:<9}  {point.speed_kn:5.1f}")
