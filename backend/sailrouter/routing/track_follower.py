from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from sailrouter.domain.great_circle import GreatCircle
from sailrouter.polar.speed_model import SpeedModel
from sailrouter.routing.mark_progress import MarkProgress
from sailrouter.weather.wind_field import WindField

STEP_S = 900.0  # 15 min
OFF_COURSE_DEG = np.arange(-90.0, 91.0, 5.0)  # headings tried around the course, to tack or gybe towards it


class TrackFollower:
    """Sails a given track in another weather: at every step the boat makes for the next track point at its best
    speed made good (VMG) towards it, i.e. tacking or gybing when the direct course is too close to the wind or
    dead downwind, with the best allowed sail, and moves on along the track by that much. Past the end of the
    track it makes for the mark it was aiming at. Measures the distance to go (through every remaining mark, e.g. the
    whole tour of an island) at given hours: what a placement is worth if this weather comes, not the best
    route in it. Manoeuvre penalties are left out (the same for every option)."""

    def __init__(self, speed_model: SpeedModel, progress: MarkProgress) -> None:
        self._speed = speed_model
        self._progress = progress

    def distances_to_go(self, track: list[tuple[float, float, int]], wind: WindField, start: datetime,
                        hours: list[float]) -> dict[float, float]:
        """track: (lat, lon, marks passed) points from the start; returns {hour: distance to go (nm)}."""
        lat, lon = track[0][0], track[0][1]
        segment, elapsed_s, results = 0, 0.0, {}
        for hour in sorted(hours):
            while elapsed_s < hour * 3600 - 1e-6:
                step_s = min(STEP_S, hour * 3600 - elapsed_s)
                moment = start + timedelta(seconds=elapsed_s)
                lat, lon, segment = self._sail(track, lat, lon, segment, wind, moment, step_s)
                elapsed_s += step_s
            leg = track[min(segment, len(track) - 1)][2]
            results[hour] = float(self._progress.distance_to_go_nm(np.array([leg]), np.array([lat]), np.array([lon]))[0])
        return results

    def _sail(self, track, lat, lon, segment, wind, moment: datetime, step_s: float):
        tws, twd = wind.wind_at(np.array([lat]), np.array([lon]), moment.timestamp())
        target = self._aim(track, segment)
        course = float(GreatCircle.bearing_deg(lat, lon, target[0], target[1]))
        headings = course + OFF_COURSE_DEG
        twa = (float(twd[0]) - headings + 180.0) % 360.0 - 180.0
        _, speed = self._speed.best(np.full(headings.shape, float(tws[0])), twa)
        made_good = float(np.max(speed * np.cos(np.radians(OFF_COURSE_DEG))))
        distance = max(made_good, 0.0) * step_s / 3600.0
        while distance > 1e-9:
            target = self._aim(track, segment)
            remaining = float(GreatCircle.distance_nm(lat, lon, target[0], target[1]))
            past_end = segment >= len(track) - 1
            if not past_end and distance >= remaining:
                lat, lon, segment, distance = target[0], target[1], segment + 1, distance - remaining
                continue
            bearing = float(GreatCircle.bearing_deg(lat, lon, target[0], target[1]))
            new_lat, new_lon = GreatCircle.destination(np.array([lat]), np.array([lon]), np.array([bearing]),
                                                       np.array([min(distance, remaining) if not past_end else distance]))
            lat, lon, distance = float(new_lat[0]), float(new_lon[0]), 0.0
        return lat, lon, segment

    def _aim(self, track, segment: int) -> tuple[float, float]:
        """The next track point, or past the end the target of the leg being sailed."""
        if segment < len(track) - 1:
            return track[segment + 1][0], track[segment + 1][1]
        leg = self._progress.legs[min(track[-1][2], len(self._progress.legs) - 1)]
        return leg.target.lat_deg, leg.target.lon_deg
