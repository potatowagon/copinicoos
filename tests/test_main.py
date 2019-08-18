import subprocess
import os
import copy
import importlib

import pytest
import psutil

from copinicoos import WorkerManager
from conftest import test_data_dir, test_dir, query_txt_path, secrets1_json_path, secrets2_json_path, MockWokerProductOnline, check_online_file_downloaded_correctly
query_everest_3_products_txt_path = os.path.join(test_data_dir, "query_everest_3_products.txt")
query_everest_6_products_txt_path = os.path.join(test_data_dir, "query_everest_6_products.txt")

copinicoos_logs_dir = os.path.join(test_dir, "copinicoos_logs")
wm_log_path = os.path.join(copinicoos_logs_dir, "WorkerManager.log")

@pytest.mark.parametrize(
    "query, login, num_expected_products", [
        ("@" + query_everest_3_products_txt_path, secrets2_json_path, 3),  
        ("@" + query_everest_6_products_txt_path, secrets2_json_path, 6),  
        ]
)
def test_mock_e2e_download(query, login, num_expected_products, creds):
    def mock_init_from_args(worker_list, args):
        mock_worker_list = [
            MockWokerProductOnline(creds["u1"] + "-1", creds["u1"], creds["p1"]),
            MockWokerProductOnline(creds["u1"] + "-2", creds["u1"], creds["p1"]),
            MockWokerProductOnline(creds["u2"] + "-1", creds["u2"], creds["p2"]),
            MockWokerProductOnline(creds["u2"] + "-2", creds["u2"], creds["p2"])
        ]
        return WorkerManager(mock_worker_list, args.query, args.total_results, args.download_location, args.polling_interval, args.offline_retries)
    
    WorkerManager.init_from_args = mock_init_from_args
    import sys
    sys.argv = ["boop", query, login, "-d", test_dir]
    import copinicoos.__main__
    importlib.reload(copinicoos.__main__)
    assert os.path.exists(os.path.join(test_dir, "copinicoos_logs"))
    assert check_online_file_downloaded_correctly() == num_expected_products

@pytest.mark.e2e
def test_e2e():
    subprocess.call(["py", "-m", "copinicoos", "@" + query_everest_3_products_txt_path, secrets2_json_path, "-d", test_dir])
    wm_log = open(wm_log_path).read()
    assert "S1A_IW_GRDH_1SDV_20190606T121404_20190606T121429_027559_031C1F_364C SUCCESS" in wm_log
    assert "S1A_IW_GRDH_1SDV_20190606T121339_20190606T121404_027559_031C1F_6EE7 SUCCESS" in wm_log
    assert "S1A_IW_GRDH_1SDV_20190602T001058_20190602T001123_027493_031A2F_CCB8 SUCCESS" in wm_log

def test_kill_and_resume():
    def get_downloaded_product_size(file_path):
        try:
            b = os.path.getsize(file_path)
            return int(b)
        except Exception as e:
            raise

    def run_and_kill(timeout=60):
        cmd = ["python", "-m", "copinicoos", "@" + query_everest_6_products_txt_path, secrets2_json_path, "-d", test_dir]
        try:
            p = subprocess.Popen(cmd)
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            p.kill()
            for i in range(0, 4):
                for proc in psutil.process_iter():
                    if proc.name() == "wget.exe":
                        parent_pid = proc.ppid()
                        print(parent_pid)
                        try:
                            proc.kill()
                        except (psutil.NoSuchProcess, ProcessLookupError) as e:
                            print(e)
                        try:
                            psutil.Process(parent_pid).kill()
                        except (psutil.NoSuchProcess, ProcessLookupError) as e:
                            print(e)
            wm_progress = open(os.path.join(copinicoos_logs_dir, "WorkerManager_progress.txt")).read()
            assert wm_progress == "4"
            for item in os.listdir(copinicoos_logs_dir):
                if not item.startswith("WorkerManager") and item.endswith("_progress.txt"):
                    worker_progress = int(open(os.path.join(copinicoos_logs_dir, item)).read())
                    assert worker_progress >= 0
                    assert worker_progress < 4
            product_size_dict = {}
            for item in os.listdir(test_dir):
                if item.startswith('S') and item.endswith(".zip"):
                    product_size_dict[item] = get_downloaded_product_size(os.path.join(test_dir, item))
            return product_size_dict

    old_product_size_dict = run_and_kill()
    new_product_size_dict = run_and_kill()

    for product, old_file_size in old_product_size_dict.items():
        new_file_size = new_product_size_dict[product]
        assert new_file_size > old_file_size