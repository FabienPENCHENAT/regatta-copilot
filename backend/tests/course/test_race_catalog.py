import json
from pathlib import Path

import pytest

from sailrouter.course.race_catalog import RaceCatalog, RaceFileError

RACES_DIR = Path(__file__).resolve().parents[3] / "races"


def test_loads_the_route_du_rhum():
    race = RaceCatalog(RACES_DIR).load("route-du-rhum-2026")
    assert race.start_time.isoformat() == "2026-11-01T12:02:00+00:00"
    class40 = race.boat("class40")
    assert class40.polar_path == "data/polars/class40-2021.vr.json"
    assert class40.start_centre.lat_deg == pytest.approx(48.73)
    gate = race.marks[0]
    assert (gate.id, gate.kind, gate.cross) == ("frehel_gate", "gate", "westward")
    assert gate.points[0].lat_deg == pytest.approx(48.696667)  # [lat, lon] order
    assert race.finish.kind == "line" and race.finish.cross == "northward"
    shapes = {zone.shape for zone in race.exclusion_zones}
    assert shapes == {"polygon", "line"}
    assert len(race.exclusion_zones) == 22


def test_lists_race_ids():
    assert "route-du-rhum-2026" in RaceCatalog(RACES_DIR).race_ids()


def test_unknown_race_and_broken_file(tmp_path):
    catalog = RaceCatalog(tmp_path)
    with pytest.raises(RaceFileError):
        catalog.load("nope")
    (tmp_path / "broken.json").write_text(json.dumps({"id": "broken", "name": "x"}))
    with pytest.raises(RaceFileError):
        catalog.load("broken")
