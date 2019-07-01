import os
import shutil

import pytest

from copinicoos import WorkerManager

def test_init_from_args(worker_list_1_worker, args):
    wm = WorkerManager.init_from_args(worker_list_1_worker, args)
    assert type(wm).__name__ == "WorkerManager"

def test_setup_workdir(worker_manager):
    worker_manager.setup_workdir()
    assert os.path.exists(os.path.join(worker_manager.workdir, 'WorkerManager_progress.txt')) == True
    shutil.rmtree(worker_manager.workdir)
