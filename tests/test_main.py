import subprocess
import os
import copy
import importlib

import pytest

from copinicoos import WorkerManager
from conftest import test_data_dir, test_dir, query_txt_path, secrets1_json_path, secrets2_json_path, MockWokerProductOnline, check_online_file_downloaded_correctly
query_everest_3_products_txt_path = os.path.join(test_data_dir, "query_everest_3_products.txt")
query_everest_6_products_txt_path = os.path.join(test_data_dir, "query_everest_6_products.txt")

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

@pytest.mark.parametrize(
    "query, login", [
        ("@" + query_txt_path, secrets2_json_path),    
        ]
)
@pytest.mark.e2e
def test_e2e(query, login):
    cmd = "py -m copinicoos"
    subprocess.call(["py", "-m", "copinicoos", query, login])