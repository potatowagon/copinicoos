"""
The Copinicoos library opens up the API for downloading Satellite images from Copernicus Hub
"""

import colorama

from .input_manager import InputManager as _InputManager
from .worker import Worker as _Worker
from .worker_manager import WorkerManager as _WorkerManager

__version__ = "0.0.1"

#__all__ = ["login"]

colorama.init(convert=True, autoreset=True)

'''
def login(**creds):
    """ Input copernicus account credentials to initialise a WorkerManager.

    Input credentials as such, for example:

    ``login(u1="username1", p1="password1", u2="username2", p2="password2")``

    will create 2 Workers and return the Workers in a list. The worker list is used to initialise WorkerManager.

    returns initialised WorkerManager class
    """

    input_manager = 
'''