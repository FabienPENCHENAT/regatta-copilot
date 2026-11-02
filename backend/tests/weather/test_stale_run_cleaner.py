import os
from datetime import UTC, datetime

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.stale_run_cleaner import StaleRunCleaner


def _runs(tmp_path, *names):
    for name in names:
        if name.endswith(".downloading"):
            (tmp_path / name).write_text("999999")
        else:
            (tmp_path / name).mkdir()
            (tmp_path / name / "f000.grib2").write_bytes(b"x")


def test_keeps_the_run_in_use_the_previous_one_and_newer_ones(tmp_path):
    _runs(tmp_path, "gefs-2026110100", "gefs-2026110106", "gefs-2026110112", "gefs-2026110118",
          "gefs-2026110106.downloading", "gfs-2026110112", "gfs-2026110118")
    os.utime(tmp_path / "gefs-2026110106.downloading", (0, 0))  # stale lock of an old run
    in_use = [ModelRun("gefs", datetime(2026, 11, 1, 12, tzinfo=UTC)),
              ModelRun("gfs", datetime(2026, 11, 1, 18, tzinfo=UTC))]
    removed = StaleRunCleaner(tmp_path).clean(in_use)
    assert sorted(removed) == ["gefs-2026110100"]
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "gefs-2026110106", "gefs-2026110106.downloading", "gefs-2026110112", "gefs-2026110118",
        "gfs-2026110112", "gfs-2026110118"]


def test_older_runs_and_their_stale_locks_go_but_a_download_in_progress_stays(tmp_path):
    _runs(tmp_path, "gefs-2026103100", "gefs-2026103100.downloading", "gefs-2026103106", "gefs-2026103106.downloading",
          "gefs-2026110112", "gefs-2026110118")
    os.utime(tmp_path / "gefs-2026103100.downloading", (0, 0))  # stale: its download crashed long ago
    removed = StaleRunCleaner(tmp_path).clean([ModelRun("gefs", datetime(2026, 11, 1, 18, tzinfo=UTC))])
    assert sorted(removed) == ["gefs-2026103100", "gefs-2026103100.downloading"]
    assert (tmp_path / "gefs-2026103106").exists()  # another process is still downloading it: left alone
