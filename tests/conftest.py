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
from zipfile import ZipFile
import re
from abc import ABC, abstractmethod

import pytest
from PIL import Image

from copinicoos import InputManager
from copinicoos.input_manager import Args 
from copinicoos import WorkerManager
from copinicoos import Worker
from copinicoos import AccountManager
from copinicoos import query_formatter

test_dir = os.path.dirname(os.path.realpath(__file__))
test_data_dir = os.path.join(test_dir, "test_data")
log_dir = os.path.join(test_dir, "copinicoos_logs")

query_txt_path = os.path.join(test_data_dir, "query.txt")
secrets1_json_path = os.path.join(test_data_dir, "secrets1.json")
secrets2_json_path = os.path.join(test_data_dir, "secrets2.json")

def close_all_loggers():
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
        logger.handlers = []

@pytest.fixture(scope="session")
def creds():
    return json.load(open(secrets2_json_path))

@pytest.fixture(scope="session")
def worker_list_2_workers(creds):
    """
    Basic worker for querying total results only
    """
    am = AccountManager()
    am.add_two_workers_per_account(creds["u1"], creds["p1"])
    return am.return_worker_list()

@pytest.fixture(scope="session")
def input_manager_with_2_workers(creds):
    im = InputManager()
    im.account_manager.add_two_workers_per_account(creds["u1"], creds["p1"])
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

@pytest.fixture(scope="session")
def formatted_worker_query_offine():
    query = open(os.path.join(test_data_dir, "offline_query_eu.txt")).read()
    return query_formatter.adjust_for_specific_product(query)

@pytest.fixture()
def worker_offline_args(formatted_worker_query_offine):
    args = Args()
    args.query = formatted_worker_query_offine
    args.total_results = 11673 
    args.download_location = test_dir
    args.offline_retries = 2
    args.polling_interval = 6
    return args

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
def worker_manager(worker_list_2_workers, wm_args):
    return WorkerManager.init_from_args(worker_list_2_workers, wm_args)

@pytest.fixture(autouse=True)
def cleanup():
    yield
    close_all_loggers()
    for item in os.listdir(test_dir):
        if item.startswith("S") and item.endswith(".zip"):
            os.remove(os.path.join(test_dir, item))
        if "_logs" in item:
            shutil.rmtree(os.path.join(test_dir, item))

def init_worker_type(worker_class, creds, creds_index,  w_args, worker_name=None, standalone=False):
    if worker_name == None:
        worker_name = creds["u" + creds_index]
    w = getattr(sys.modules[__name__], worker_class)(worker_name, creds["u" + creds_index], creds["p" + creds_index])
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

@pytest.fixture()
def worker_download_incomplete1(creds, w_args):
    return init_worker_type("MockWokerIncompleteProductOnline", creds, "1", w_args)

###### Workers capable of running in stand alone mode 
@pytest.fixture()
def real_offline_worker(creds, worker_offline_args):
    w = init_worker_type("Worker", creds, "1", worker_offline_args, standalone=True)
    return w

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

class MockWorker(Worker, ABC):
    @property
    @abstractmethod
    def mock_product_uri(self):
        pass

    def query_product_size(self, product_uri):
        ''' Always query the file size of self.product_uri
        Args:
            product uri (str): doenst matter, just to fit the api
        Returns:
            product file size in bytes (int) or None if self.product_uri query failed
        '''
        product_uri = "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_offline.zip?raw=true"
        try:
            cmd = ["wget", "--spider", "--user=" + self.username, "--password=" + self.password, self.mock_product_uri]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            m = re.search(r'(?<=Length: )\d+', str(out))
            length = int(m.group(0))
            return length
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Error in querying product size for " + self.mock_product_uri)
            return None

    def download_product(self, file_path, product_uri):
        try:
            cmd = ["wget", "-O", file_path, "--continue", self.mock_product_uri]
            self.logger.info(cmd)
            proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True, universal_newlines=True)
            return proc
        except Exception as e:
            raise
    
    def mock_log_download_progress(self, proc):
        self._log_download_progress(proc, "Mock product", self.query_product_size(self.mock_product_uri))
            
class MockWokerProductOffline(MockWorker):
    mock_product_uri = "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_offline.zip?raw=true"


class MockWokerProductOnline(MockWorker):
    mock_product_uri = "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_online.zip?raw=true"

class MockWokerIncompleteProductOnline(MockWokerProductOnline):
    def query_product_size(self, product_uri):
        '''Returns some incredibly large mock file size'''
        return 9999999999999999

def check_online_file_downloaded_correctly():
    '''Fail test case if mock online file cannot be opened
    
    Returns:
        count (int): number of mock online files downloaded if all downloaded correctly 
    '''
    count = 0
    for item in os.listdir(test_dir):
        if item.startswith("S") and item.endswith(".zip"):
            count += 1
            mock_product = ZipFile(os.path.join(test_dir, item))
            with mock_product.open("S1A_online/tiny_file.txt") as txt_file:
                txt = str(txt_file.read())
                assert "this is just to occupy disk space." in txt
                txt_file.close()

            with mock_product.open('S1A_online/fatter_file.png') as img_file:
                try:
                    img = Image.open(img_file)
                    img.verify()
                    img_file.close()
                except Exception as e:
                    pytest.fail(e)
    return count