"""
reusable fixtures are here
"""
import json
import os
import shutil
import logging
import sys
import subprocess
import time

import pytest

from copinicoos import InputManager
from copinicoos.input_manager import Args 
from copinicoos import WorkerManager
from copinicoos.worker import Worker

test_dir = os.path.dirname(os.path.realpath(__file__))
test_data_dir = os.path.join(test_dir, "test_data")
log_dir = os.path.join(test_dir, "copinicoos_logs")

def close_all_loggers():
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    print(loggers)
    for logger in loggers:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers = []

@pytest.fixture(scope="session")
def creds():
    return json.load(open(os.path.join(test_data_dir, "secrets2.json")))

@pytest.fixture(scope="session")
def worker_list_1_worker(creds):
    """
    Basic worker for querying total results only
    """
    im = InputManager()
    im.add_worker(creds["u1"], creds["p1"])
    return im.worker_list

@pytest.fixture()
def input_manager_with_one_worker(worker_list_1_worker):
    im = InputManager()
    im.worker_list = worker_list_1_worker
    return im

@pytest.fixture(scope="session")
def query():
    return open(os.path.join(test_data_dir, "query.txt")).read()

@pytest.fixture(scope="session")
def formatted_query():
    return 'https://scihub.copernicus.eu/dhus/search?q=( footprint:\"Intersects(POLYGON((91.45532862800384 22.42016942838278,91.34620270146559 22.43895934481047,91.32598614177974 22.336847270362682,91.4350291249018 22.31804599405974,91.45532862800384 22.42016942838278)))\" ) AND ( (platformname:Sentinel-1 AND producttype:GRD))&format=json'

@pytest.fixture(scope="session")
def formatted_query1():
    return 'https://scihub.copernicus.eu/dhus/search?q=( footprint:\"Intersects(POLYGON((91.45532862800384 22.42016942838278,91.34620270146559 22.43895934481047,91.32598614177974 22.336847270362682,91.4350291249018 22.31804599405974,91.45532862800384 22.42016942838278)))\" ) AND ( (platformname:Sentinel-1 AND producttype:GRD))&format=json&rows=1&start='

@pytest.fixture()
def w_args(formatted_query1):
    args = Args()
    args.query = formatted_query1
    args.total_results = 200
    args.download_location = test_dir
    args.offline_retries = 2
    args.polling_interval = 6
    return args

@pytest.fixture()
def wm_args(formatted_query):
    args = Args()
    args.query = formatted_query
    args.total_results = 200
    args.download_location = test_dir
    args.offline_retries = 2
    args.polling_interval = 6
    return args

@pytest.fixture()
def worker_manager(worker_list_1_worker, wm_args):
    return WorkerManager.init_from_args(worker_list_1_worker, wm_args)

@pytest.fixture(autouse=True)
def cleanup():
    yield
    close_all_loggers()
    for item in os.listdir(test_dir):
        if item.startswith("S") and item.endswith(".zip"):
            os.remove(os.path.join(test_dir, item))
        if "_logs" in item:
            shutil.rmtree(os.path.join(test_dir, item))

def init_worker_type(worker_class, creds, creds_index,  w_args, standalone=False):
    w = getattr(sys.modules[__name__], worker_class)(creds["u" + creds_index], creds["p" + creds_index])
    w.register_settings(w_args.query, w_args.download_location, w_args.polling_interval, w_args.offline_retries)
    if standalone:
        logdir = os.path.join(test_dir, w.name + "_logs")
        if not os.path.exists(logdir):
            os.mkdir(logdir)
        w.setup(logdir)
    return w

@pytest.fixture()
def worker1(creds, w_args):
    w = init_worker_type("Worker", creds, "1", w_args)
    return w

@pytest.fixture()
def worker2(creds, w_args):
    w = init_worker_type("Worker", creds, "2", w_args)
    return w

@pytest.fixture()
def worker_download_offline1(creds, w_args):
    return init_worker_type("MockWokerProductOffline", creds, "1", w_args)
    
@pytest.fixture()
def worker_download_online1(creds, w_args):
    return init_worker_type("MockWokerProductOnline", creds, "1", w_args)

@pytest.fixture()
def worker_download_online2(creds, w_args):
    return init_worker_type("MockWokerProductOnline", creds, "2", w_args)

@pytest.fixture()
def worker_download_offline2(creds, w_args):
    return init_worker_type("MockWokerProductOffline", creds, "2", w_args)

###### Workers capable of running in stand alone mode 
@pytest.fixture()
def standalone_worker1(creds, w_args):
    w = init_worker_type("Worker", creds, "1", w_args, standalone=True)
    return w

@pytest.fixture()
def standalone_worker2(creds, w_args):
    w = init_worker_type("Worker", creds, "2", w_args, standalone=True)
    return w

@pytest.fixture()
def standalone_worker_download_offline1(creds, w_args):
    return init_worker_type("MockWokerProductOffline", creds, "1", w_args, standalone=True)
    
@pytest.fixture()
def standalone_worker_download_online1(creds, w_args):
    return init_worker_type("MockWokerProductOnline", creds, "1", w_args, standalone=True)

@pytest.fixture()
def standalone_worker_download_online2(creds, w_args):
    return init_worker_type("MockWokerProductOnline", creds, "2", w_args, standalone=True)

@pytest.fixture()
def standalone_worker_download_offline2(creds, w_args):
    return init_worker_type("MockWokerProductOffline", creds, "2", w_args, standalone=True)
            
class MockWokerProductOffline(Worker):
    def download_product(self, file_path, product_uri):
        try:
            product_uri =  "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_offline.zip?raw=true"
            cmd = ["wget", "-O", file_path, "--continue", product_uri]
            self.logger.info(cmd)
            subprocess.call(cmd)
        except Exception as e:
            raise

class MockWokerProductOnline(Worker):
    def download_product(self, file_path, product_uri):
        try:
            product_uri =  "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_online.zip?raw=true"
            cmd = ["wget", "-O", file_path, "--continue", product_uri]
            self.logger.info(cmd)
            subprocess.call(cmd)
        except Exception as e:
            raise
