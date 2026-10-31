import os
import time
from datetime import UTC, datetime

from sailrouter.weather.model_run import ModelRun
from sailrouter.weather.run_download_lock import RunDownloadLock

RUN = ModelRun("gefs", datetime(2026, 10, 31, 6, tzinfo=UTC))


def test_own_lock_does_not_block_and_release_frees_it(tmp_path):
    lock = RunDownloadLock(tmp_path)
    lock.touch(RUN)
    assert lock.path(RUN).name == "gefs-2026103106.downloading"
    assert not lock.held_by_other(RUN)
    lock.release(RUN)
    assert not lock.path(RUN).exists()


def test_fresh_lock_of_another_process_blocks_until_it_goes_stale(tmp_path):
    lock = RunDownloadLock(tmp_path, stale_after_s=60)
    lock.path(RUN).write_text(str(os.getpid() + 1))
    assert lock.held_by_other(RUN)
    old = time.time() - 120
    os.utime(lock.path(RUN), (old, old))
    assert not lock.held_by_other(RUN)
