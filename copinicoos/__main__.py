import sys
import asyncio

from .input_manager import InputManager
from .worker_manager import WorkerManager

input_manager = InputManager()
if len(sys.argv) == 1:
    input_manager.interactive_input()
else:
    input_manager.cmd_input()

worker_manager = WorkerManager.init_from_args(input_manager.return_worker_list(), input_manager.return_args())
worker_manager.setup_workdir()
asyncio.run(worker_manager.run_workers())