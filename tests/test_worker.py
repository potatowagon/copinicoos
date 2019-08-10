import os
import random
import re
from zipfile import ZipFile

import pytest
from PIL import Image

from conftest import test_data_dir, test_dir

@pytest.mark.parametrize(
    "result_num", [
        (1),
        (60),
        (150)
    ]
)
def test_query_product_uri_success(standalone_worker1, result_num):
    title, product_uri = standalone_worker1.query_product_uri(result_num)
    try:
        assert title.startswith("S") 
        assert product_uri.startswith('https://scihub.copernicus.eu/dhus/odata/v1/Products(') 
        assert product_uri.endswith('/$value') 
    except Exception as e:
        print(title, product_uri)
        raise

def test_download_began(standalone_worker1):
    assert standalone_worker1.download_began(os.path.join(test_data_dir, "S1A_offline.zip")) == False
    assert standalone_worker1.download_began(os.path.join(test_data_dir, "S1A_online.zip")) == True

@pytest.mark.timeout(120)
@pytest.mark.skip(reason="hitting too many online products")
@pytest.mark.parametrize(
    "result_num", [
        (random.randint(150,300))
    ]
)
def test_run_offline(standalone_worker1, result_num):
    standalone_worker1.run(result_num)
    log = standalone_worker1.get_log()
    assert "Product could be offline. Retrying after " in log

def test_run_offline_mock(standalone_worker_download_offline1):
    test_run_offline(standalone_worker_download_offline1, 0)

def test_fixture_worker_download_offline(standalone_worker_download_offline1):
    w = standalone_worker_download_offline1
    file_path = os.path.join(w.download_location, "S1A_offline.zip")
    w.download_product(file_path, "bla bla")
    assert os.path.exists(file_path) == True

def test_fixture_worker_download_online(standalone_worker_download_online1):
    w = standalone_worker_download_online1
    downloaded_file_path = os.path.join(w.download_location, "S1A_online.zip")
    w.download_product(downloaded_file_path, "bla bla")
    assert os.path.exists(downloaded_file_path) == True
    log = w.get_log()
    assert "https://github.com/potatowagon/copinicoos" in log

def setup_worker_manager(worker_manager, worker_list):
    worker_manager.worker_list = worker_list
    worker_manager.setup_workdir()
    return worker_manager

@pytest.mark.timeout(300)
def test_run_in_seperate_process_one_worker(worker_manager, worker_download_online1):
    wm = setup_worker_manager(worker_manager, [worker_download_online1])
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs", worker_download_online1.name + ".log"))
    # download first 3 results
    wm.total_results = 3
    wm.run_workers()
    log = worker_download_online1.get_log()
    assert "Begin downloading" in log 
    assert "Downloaded product " in log
    if "DEBUG" in log:
        assert "lock" in log 
    assert wm.get_log().count("SUCCESS") == wm.total_results

@pytest.mark.timeout(300)
def test_run_in_seperate_process_one_worker_offline(worker_manager, worker_download_offline1):
    wm = setup_worker_manager(worker_manager, [worker_download_offline1])
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs", worker_download_offline1.name + ".log"))
    # download first 3 results
    wm.total_results = 3
    wm.run_workers()
    log = worker_download_offline1.get_log()
    total_retries = wm.total_results * worker_download_offline1.offline_retries
    assert log.count("Retry attempt") == total_retries
    download_attempts = total_retries + wm.total_results
    assert log.count("Begin downloading") == download_attempts
    assert log.count("Product could be offline.") == download_attempts
    if "DEBUG" in log:
        assert "lock" in log 
    
def check_online_file_downloaded_correctly():
    for item in os.listdir(test_dir):
        if item.startswith("S") and item.endswith(".zip"):
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
            
@pytest.mark.timeout(300)
def test_run_in_seperate_process_two_workers_both_online(worker_manager, worker_download_online1, worker_download_online2):
    wm = setup_worker_manager(worker_manager, [worker_download_online1, worker_download_online2])
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs", worker_download_online1.name + ".log"))
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs", worker_download_online2.name + ".log"))
    # download first 3 results
    wm.total_results = 3
    wm.run_workers()

    combined_log = ""

    for worker in wm.worker_list:
        log = worker.get_log()
        assert "Begin downloading" in log 
        assert "Downloaded product " in log
        if "DEBUG" in log:
            assert "lock" in log
        combined_log += log 
        
    assert combined_log.count("Downloaded product") == wm.total_results
    check_online_file_downloaded_correctly()

    assert wm.get_log().count("SUCCESS") == wm.total_results



