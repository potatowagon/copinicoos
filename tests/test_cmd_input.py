import subprocess

import pytest

from copinicoos import InputManager

@pytest.mark.parametrize(
    "query, login", [
        ("@query.txt", "@secrets1.json"),
        ("@query.txt", "secrets1.json"),
        ("@query.txt", "secrets2.json"),
    ]
)
def test_unit(query, login):
    im = InputManager()
    im.cmd_input(test_args=[query, login])

@pytest.mark.parametrize(
    "query, login", [
        ("@query.txt", "@secrets1.json"),
        ("@query.txt", "secrets1.json"),
        ("@query.txt", "secrets2.json"),
    ]
)
def test_successful_login_from_cli(query, login):
    cmd = "py -m copinicoos"
    subprocess.call(["py", "-m", "copinicoos", query, login])