import sys

from .input_manager import InputManager
from .worker_manager import WorkerManager
from . import wget_check

if not wget_check.is_wget_installed:
    wget_check.install_wget()

input_manager = InputManager()
if len(sys.argv) == 1:
    input_manager.interactive_input()
else:
    input_manager.cmd_input()

worker_manager = WorkerManager.init_from_args(input_manager.return_worker_list(), input_manager.return_args())
worker_manager.setup_workdir()
worker_manager.run_workers()