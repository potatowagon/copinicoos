import os
import random
import asyncio
import re

import pytest

from conftest import test_data_dir, test_dir

@pytest.mark.parametrize(
    "result_num", [
        (1),
        (60),
        (150)
    ]
)
def test_query_product_uri_success(worker1, result_num):
    title, product_uri = worker1.query_product_uri(result_num)
    try:
        assert title.startswith("S") 
        assert product_uri.startswith('"https://scihub.copernicus.eu/dhus/odata/v1/Products(') 
        assert product_uri.endswith('/$value"') 
    except Exception as e:
        print(title, product_uri)
        raise

def test_download_began(worker1):
    assert worker1.download_began(os.path.join(test_data_dir, "S1A_offline.zip")) == False
    assert worker1.download_began(os.path.join(test_data_dir, "S1A_online.zip")) == True

@pytest.mark.parametrize(
    "result_num", [
        (random.randint(150,200))
    ]
)
def test_run_offline(worker1, result_num):
    worker1.run(result_num)
    log = worker1.get_log()
    assert "Product could be offline. Retrying after " in log

def test_run_offline_mock(worker_download_offline1):
    test_run_offline(worker_download_offline1, 0)

def test_fixture_worker_download_offline(worker_download_offline1):
    w = worker_download_offline1
    file_path = os.path.join(w.download_location, "S1A_offline.zip")
    w.download_product(file_path, "bla bla")
    assert os.path.exists(file_path) == True
    assert file_path in  w.get_log()

def test_fixture_worker_download_online(worker_download_online1):
    w = worker_download_online1
    downloaded_file_path = os.path.join(w.download_location, "S1A_online.zip")
    w.download_product(downloaded_file_path, "bla bla")
    assert os.path.exists(downloaded_file_path) == True
    log = w.get_log()
    assert downloaded_file_path in log
    assert "https://github.com/potatowagon/copinicoos" in log

def setup_worker_manager(worker_manager, worker_list):
    worker_manager.worker_list = worker_list
    worker_manager.setup_workdir()
    return worker_manager

def test_run_in_seperate_process_one_worker(worker_manager, worker_download_online1):
    wm = setup_worker_manager(worker_manager, [worker_download_online1])
    # download first 3 results
    wm.total_results = 3
    asyncio.run(wm.run_workers())
    log = worker_download_online1.get_log()
    assert "Begin downloading" in log 
    assert "Downloaded product " in log
    if "DEBUG" in log:
        assert "lock" in log 

def test_run_in_seperate_process_one_worker_offline(worker_manager, worker_download_offline1):
    wm = setup_worker_manager(worker_manager, [worker_download_offline1])
    # download first 3 results
    wm.total_results = 3
    asyncio.run(wm.run_workers())
    log = worker_download_offline1.get_log()
    total_retries = wm.total_results * worker_download_offline1.offline_retries
    assert log.count("Retry attempt") == total_retries
    download_attempts = total_retries + wm.total_results
    assert log.count("Begin downloading") == download_attempts
    assert log.count("Product could be offline.") == download_attempts
    if "DEBUG" in log:
        assert "lock" in log 
