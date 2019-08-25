import os
import random
import re
import subprocess
import time
import sys

import pytest

from copinicoos import Worker
from conftest import test_data_dir, test_dir, check_online_file_downloaded_correctly

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

@pytest.mark.timeout(120)
def test_run_offline(real_offline_worker):
    result_num = random.randint(2, 11673)
    real_offline_worker.run(result_num)
    log = real_offline_worker.get_log()
    assert "Product could be offline. Retrying after " in log

def test_run_offline_mock(standalone_worker_download_offline1):
    standalone_worker_download_offline1.run(0)

def test_fixture_mock_worker_query_offline_product_size(standalone_worker_download_offline1):
    assert standalone_worker_download_offline1.query_product_size("this shouldnt matter, because its a mock") == 0

def test_fixture_mock_worker_download_offline(standalone_worker_download_offline1):
    w = standalone_worker_download_offline1
    file_path = os.path.join(w.download_location, "S1A_offline.zip")
    proc = w.download_product(file_path, "bla bla")
    w.mock_log_download_progress(proc)
    assert os.path.exists(file_path) == True

def test_fixture_mock_worker_query_online_product_size(standalone_worker_download_online1):
    assert standalone_worker_download_online1.query_product_size("this shouldnt matter, because its a mock") == 759842

def test_fixture_mock_worker_download_online(standalone_worker_download_online1):
    w = standalone_worker_download_online1
    downloaded_file_path = os.path.join(w.download_location, "S1A_online.zip")
    proc = w.download_product(downloaded_file_path, "bla bla")
    w.mock_log_download_progress(proc)
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
    download_attempts = total_retries + wm.total_results
    assert log.count("Begin downloading") == download_attempts
    assert log.count("Product could be offline.") == download_attempts
    if "DEBUG" in log:
        assert "lock" in log 

@pytest.mark.timeout(300)
def test_run_in_seperate_process_one_worker_online_incomplete(worker_manager, worker_download_incomplete1):
    wm = setup_worker_manager(worker_manager, [worker_download_incomplete1])
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs", worker_download_incomplete1.name + ".log"))
    # download first 3 results
    wm.total_results = 3
    wm.run_workers()
    log = worker_download_incomplete1.get_log()
    total_retries = wm.total_results * worker_download_incomplete1.offline_retries
    download_attempts = total_retries + wm.total_results
    assert log.count("Begin downloading") == download_attempts
    assert log.count("There was a break in connection.") == download_attempts
    if "DEBUG" in log:
        assert "lock" in log 
    wm_log = wm.get_log()
    assert wm_log.count("FAILED") == wm.total_results
            
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

@pytest.mark.parametrize(
    "sample_product_uri, expected_length_in_bytes", [
        ("https://scihub.copernicus.eu/dhus/odata/v1/Products(\'23759763-91e8-4336-a50a-a143e14c8d69\')/$value", 993398956),
        ("https://scihub.copernicus.eu/dhus/odata/v1/Products(\'05d5daa5-c1aa-4ad6-a600-d39e9a692db5\')/$value", 1049855358),
        ("https://blabla", None),
        ("https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_offline.zip?raw=true", 0),
        ("https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_online.zip?raw=true", 759842)
    ]
)
def test_query_product_size(sample_product_uri, expected_length_in_bytes, standalone_worker1):
    assert standalone_worker1.query_product_size(sample_product_uri) == expected_length_in_bytes

@pytest.mark.parametrize(
    "file_path, expected_length_in_bytes", [
        (os.path.join(test_data_dir, "S1A_offline.zip"), 0),
        (os.path.join(test_data_dir, "S1A_online.zip"), 759842)
    ]
)
def test_get_downloaded_product_size(file_path, expected_length_in_bytes, standalone_worker1):
    assert standalone_worker1.get_downloaded_product_size(file_path) == expected_length_in_bytes

def test_regex_match_download_bar():
    out = "Saving to: 'C:/Users/Sherry/Desktop/nus/FYP-20180824T033439Z-001/copernicus/copinicoos/tests/S1A_online.zip'\n\nC:/Users/Sherry/Desktop/nus/FYP-201808 100%[=========================================================================>] 742.03K  --.-KB/s    in 0.1s\n\n2019-08-24 18:04:36 (7.62 MB/s) - 'C:/Users/Sherry/Desktop/nus/FYP-20180824T033439Z-001/copernicus/copinicoos/tests/S1A_online.zip' saved [759842/759842]"
    regex = r'\d+%\[.*\].*\n'
    m = re.search(regex, out)
    print('\n')
    print(m.group(0))

def test_assign_colours():
    worker0 = Worker("worker0", "u0", "p0")
    worker1 = Worker("worker1", "u1", "p1")
    worker2 = Worker("worker2", "u2", "p2")
    worker3 = Worker("worker3", "u3", "p3")
    worker4 = Worker("worker4", "u4", "p4")
    worker5 = Worker("worker5", "u5", "p5")
    worker6 = Worker("worker6", "u6", "p6")
    worker7 = Worker("worker7", "u7", "p7")

    Worker.assign_colours()
    for worker in Worker.worker_instances_list:
        print(worker.colour + "This is the colour of " + worker.name)

    old_list_len = len(Worker.worker_instances_list)
    assert worker0 in Worker.worker_instances_list 
    worker0.__del__()
    assert len(Worker.worker_instances_list) + 1 ==  old_list_len

@pytest.mark.skip(reason="this is a draft")
def test_wget_output_subprocess():
    mock_product_uri =  "https://github.com/potatowagon/copinicoos/blob/remove-dhusget/tests/test_data/S1A_online.zip?raw=true"
    cmd = ["wget", "-O", os.path.join(test_dir, 'S1A_IW_GRDH_1SDV_20190521T001122_20190521T001147_027318_0314BE_D75D.zip'), "--continue", mock_product_uri]
    real_product = "wget -O C:\\Users\\Sherry\\Desktop\\nus\\FYP-20180824T033439Z-001\\copernicus\\copinicoos\\tests\\S1A_IW_GRDH_1SDV_20190521T001122_20190521T001147_027318_0314BE_D75D.zip --continue --user=copinicoos1 --password=sondra11 https://scihub.copernicus.eu/dhus/odata/v1/Products('05d5daa5-c1aa-4ad6-a600-d39e9a692db5')/$value"
    proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True, universal_newlines=True)
    #proc = subprocess.Popen(real_product, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True)
    print("here")
    logged = []
    while proc.poll() is None:
        line = proc.stdout.readline()
        print(line)
        if line:
            try:
                 response = re.search(r'HTTP request sent, awaiting response... .+', line).group(0)
                 print(response)
            except AttributeError as e:
                pass
            try:
                progress_perc = r'\d+%'
                progress_perc = re.search(progress_perc, line).group(0)
                time_left = r'(\d+[hms])+'
                time_left = re.search(time_left, line).group(0)
                downloaded = r'\d+[KM]'
                downloaded = re.search(downloaded, line).group(0)
                print('Progress: ' + progress_perc + ' Time left: ' + time_left + ' Downloaded: ' + downloaded)
            except AttributeError as e:
                print(e)
        else:
            print(proc.poll())