import json
import os

import pytest

from copinicoos import InputManager
from copinicoos import input_manager
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

def test_interactive_input(capsys, creds, query):
    input_values = [
        2,
        creds["u1"],
        creds["p1"],
        creds["u2"],
        creds["p2"],
        query,
        "\n",
        "\n",
        "\n"
    ]
    im = InputManager()
    def mock_input():
        return input_values.pop(0)
    input_manager.input = mock_input
    im.interactive_input()
    out, err = capsys.readouterr()
    assert "Enter number of accounts:" in out
    assert "Enter username of account" in out
    assert "Enter password of account" in out
    assert "Authenticating worker..." in out
    assert "Worker sucessfully authenticated." in out
    assert "Enter query:" in out
    assert "products found" in out
    assert "Default download directory set to" in out
    assert "Enter new path" in out
    assert "Default polling interval" in out
    assert "Enter new polling interval" in out
    assert "Default offline retries" in out
    assert "Enter new offline retries" in out

    args = im.return_args() 
    assert type(args).__name__ == "Args"
    assert len(im.return_worker_list()) == 4
    
