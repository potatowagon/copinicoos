import pytest

from copinicoos import secure

def test_encrypt_decrypt():
    assert secure.decrypt("bloop", secure.encrypt("bloop", "blaap")) == "blaap"
    