import json
import os

import pytest

from copinicoos import InputManager
from conftest import test_data_dir, test_dir

def test_add_worker_success(creds):
    im = InputManager()
    assert im.add_worker(creds["u1"], creds["p1"]) == True
    assert len(im.worker_list) == 1
    assert type(im.worker_list[0]).__name__ == "Worker"

def test_add_worker_wrong_creds():
    im = InputManager()
    assert im.add_worker("nada", "zip") == False
    assert len(im.worker_list) == 0

def test_multi_add_worker_success(creds):
    im = InputManager()
    assert im.add_worker(creds["u1"], creds["p1"]) == True
    assert im.add_worker(creds["u2"], creds["p2"]) == True
    assert len(im.worker_list) == 2

def test_multi_add_worker_repeat_creds(creds):
    im = InputManager()
    assert im.add_worker(creds["u1"], creds["p1"]) == True
    assert im.add_worker(creds["u1"], creds["p1"]) == False
    assert len(im.worker_list) == 1

def test_get_total_results_from_query_success(query, input_manager_with_one_worker):
    im = input_manager_with_one_worker
    tr = im.get_total_results_from_query(query)
    print(str(tr))
    assert type(im.args.total_results) is int
    assert type(tr) is int
    assert tr == im.args.total_results
    assert tr > 0 

@pytest.mark.parametrize(
    "arg", [
        (os.path.join(test_data_dir,"secrets1.json")),
        ('{"u1": "username", "p1": "password"}'),
        ('{"u1":"username"  ,\n "p1":"password"}'),
        ('{\n"u1" : "  username"  ,\n "p1":"password"\n}'),
        (open(os.path.join(test_data_dir,'secrets2.json')).read())    
    ]
)
def test_get_json_creds_success(arg):
    im = InputManager()
    out = im.get_json_creds(arg)
    assert type(out) == dict

@pytest.mark.parametrize(
    "arg", [
        ("badfile.json")
    ]
)
def test_get_json_creds_badfile(arg):
    im = InputManager()
    with pytest.raises(Exception) as e:
        im.get_json_creds(arg)
    assert "No such file or directory" in str(e.value)

@pytest.mark.parametrize(
    "json, expected_workers", [
        (json.load(open(os.path.join(test_data_dir,'secrets1.json'))), 1),
        (json.load(open(os.path.join(test_data_dir,'secrets2.json'))), 2)
    ]
)
def test_add_workers_from_json_creds(json, expected_workers):
    im = InputManager()
    im.add_workers_from_json_creds(json)
    assert len(im.worker_list) == expected_workers
    for worker in im.worker_list:
        assert type(worker).__name__ == "Worker"
