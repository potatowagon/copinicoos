import os
import shutil

import pytest

from copinicoos import WorkerManager

def test_init_from_args(worker_list_2_workers, wm_args):
    wm = WorkerManager.init_from_args(worker_list_2_workers, wm_args)
    assert type(wm).__name__ == "WorkerManager"

def test_setup_workdir(worker_manager):
    worker_manager.setup_workdir()
    assert os.path.exists(os.path.join(worker_manager.workdir, 'WorkerManager_progress.txt'))
    assert os.path.exists(os.path.join(worker_manager.workdir, 'config.json'))

