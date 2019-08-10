import json
import os

import pytest

from copinicoos import InputManager
from conftest import test_data_dir, test_dir

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
