"""
The Copinicoos library opens up the API for downloading Satellite images from Copernicus Hub
"""

import colorama

from .input_manager import InputManager
from .worker import Worker as Worker
from .worker_manager import WorkerManager 
from .account_manager import AccountManager

__version__ = "0.0.1"

colorama.init(convert=True, autoreset=True)