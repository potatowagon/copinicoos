import json
import os

import pytest

from copinicoos import InputManager
from conftest import query_txt_path, secrets1_json_path, secrets2_json_path

@pytest.mark.parametrize(
    "query, login", [
        ("@" + query_txt_path, "@" + secrets1_json_path),
        ("@" + query_txt_path, secrets1_json_path),
        ("@" + query_txt_path, secrets2_json_path),
    ]
)
def test_cmd_input(query, login):
    im = InputManager()
    im.cmd_input(test_args=[query, login])
    args = im.return_args()
    assert type(args).__name__ == "Args"

def test_get_total_results_from_query_success(query, input_manager_with_2_workers):
    im = input_manager_with_2_workers
    tr = im.get_total_results_from_query(query)
    print(str(tr))
    assert type(im.args.total_results) is int
    assert type(tr) is int
    assert tr == im.args.total_results
    assert tr > 0 

@pytest.mark.parametrize(
    "arg", [
        (secrets1_json_path),
        ('{"u1": "username", "p1": "password"}'),
        ('{"u1":"username"  ,\n "p1":"password"}'),
        ('{\n"u1" : "  username"  ,\n "p1":"password"\n}'),
        (open(secrets2_json_path).read())    
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
