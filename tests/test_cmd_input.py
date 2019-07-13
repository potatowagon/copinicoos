import subprocess
import os

import pytest

from copinicoos import InputManager
from conftest import test_data_dir

query_txt_path = os.path.join(test_data_dir, "query.txt")
secrets1_json_path = os.path.join(test_data_dir, "secrets1.json")
secrets2_json_path = os.path.join(test_data_dir, "secrets2.json")

@pytest.mark.parametrize(
    "query, login", [
        ("@" + query_txt_path, "@" + secrets1_json_path),
        ("@" + query_txt_path, secrets1_json_path),
        ("@" + query_txt_path, secrets2_json_path),
    ]
)
def test_unit(query, login):
    im = InputManager()
    im.cmd_input(test_args=[query, login])

@pytest.mark.parametrize(
    "query, login", [
        ("@" + query_txt_path, "@" + secrets1_json_path),
        ("@" + query_txt_path, secrets1_json_path),
        ("@" + query_txt_path, secrets2_json_path),    
        ]
)
def test_successful_login_from_cli(query, login):
    cmd = "py -m copinicoos"
    subprocess.call(["py", "-m", "copinicoos", query, login])