"""
reusable fixtures are here
"""
import json
import os
import shutil

import pytest

from copinicoos import InputManager
from copinicoos.input_manager import Args 
from copinicoos import WorkerManager

@pytest.fixture(scope="session")
def creds():
    return json.load(open("secrets2.json"))

@pytest.fixture(scope="session")
def worker_list_1_worker(creds):
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
    return open("query.txt").read()

@pytest.fixture(scope="session")
def formatted_query():
    return '"https://scihub.copernicus.eu/dhus/search?q=( footprint:\\"Intersects(POLYGON((91.45532862800384 22.42016942838278,91.34620270146559 22.43895934481047,91.32598614177974 22.336847270362682,91.4350291249018 22.31804599405974,91.45532862800384 22.42016942838278)))\\" ) AND ( (platformname:Sentinel-1 AND producttype:GRD))&format=json"'

@pytest.fixture()
def args(formatted_query):
    args = Args()
    args.query = formatted_query
    args.total_results = 200
    args.download_location = os.getcwd()
    args.offline_retries = 2
    args.polling_interval = 6
    return args

@pytest.fixture()
def worker_manager(worker_list_1_worker, args):
    return WorkerManager.init_from_args(worker_list_1_worker, args)

@pytest.fixture()
def cleanup():
    yield
    test_dir = os.path.dirname(os.path.realpath(__file__))
    for item in os.listdir(test_dir):
        if item.startswith("S") and item.endswith(".zip"):
            os.remove(os.path.join(test_dir, item))
        if item == "copinicoos_logs":
            shutil.rmtree(item)

            