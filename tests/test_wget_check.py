import pytest

from copinicoos import wget_check

def test_is_wget_installed():
    assert wget_check.is_wget_installed()

def test_is_choco_installed():
    assert wget_check.is_choco_installed() == wget_check.is_windows()

def test_install_choco():
    if wget_check.is_windows():
        wget_check.install_choco()

def test_install_wget():
    wget_check.install_wget()
