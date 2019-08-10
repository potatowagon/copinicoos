import subprocess
import os

import pytest

from copinicoos import InputManager
from conftest import query_txt_path, secrets1_json_path, secrets2_json_path

@pytest.mark.parametrize(
    "query, login", [
        ("@" + query_txt_path, secrets2_json_path),    
        ]
)
@pytest.mark.e2e
def test_successful_login_from_cli(query, login):
    cmd = "py -m copinicoos"
    subprocess.call(["py", "-m", "copinicoos", query, login])