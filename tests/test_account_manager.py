import json
import os

import pytest

from copinicoos import AccountManager
from conftest import test_data_dir, test_dir

def test_add_two_workers_per_account_success(creds):
    am = AccountManager()
    assert am.add_two_workers_per_account(creds["u1"], creds["p1"]) == True
    assert len(am.worker_list) == 2
    for worker in am.worker_list:
        assert type(worker).__name__ == "Worker"
    assert am.worker_list[0].name == creds["u1"] + "-1"
    assert am.worker_list[1].name == creds["u1"] + "-2"

def test_add_two_workers_per_account_wrong_creds():
    am = AccountManager()
    assert am.add_two_workers_per_account("nada", "zip") == False
    assert len(am.worker_list) == 0

def test_add_two_workers_per_account_multi_success(creds):
    am = AccountManager()
    assert am.add_two_workers_per_account(creds["u1"], creds["p1"]) == True
    assert am.add_two_workers_per_account(creds["u2"], creds["p2"]) == True
    assert len(am.worker_list) == 4
    for worker in am.worker_list:
        assert type(worker).__name__ == "Worker"
    assert am.worker_list[0].name == creds["u1"] + "-1"
    assert am.worker_list[1].name == creds["u1"] + "-2"
    assert am.worker_list[2].name == creds["u2"] + "-1"
    assert am.worker_list[3].name == creds["u2"] + "-2"

def test_add_two_workers_per_account_repeat_creds(creds):
    am = AccountManager()
    assert am.add_two_workers_per_account(creds["u1"], creds["p1"]) == True
    assert am.add_two_workers_per_account(creds["u1"], creds["p1"]) == False
    assert len(am.worker_list) == 2

@pytest.mark.parametrize(
    "json, expected_workers", [
        (json.load(open(os.path.join(test_data_dir,'secrets1.json'))), 2),
        (json.load(open(os.path.join(test_data_dir,'secrets2.json'))), 4)
    ]
)
def test_add_workers_from_json_creds(json, expected_workers):
    am = AccountManager()
    am.add_workers_from_json_creds(json)
    assert len(am.worker_list) == expected_workers
    for worker in am.worker_list:
        assert type(worker).__name__ == "Worker"

def test_return_worker_list():
    am = AccountManager()
    assert am.return_worker_list() == None
   