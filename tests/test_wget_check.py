import subprocess

import pytest

from copinicoos import wget_check

def test_is_wget_installed():
    assert wget_check.is_wget_installed()

def test_is_choco_installed():
    assert wget_check.is_choco_installed() == wget_check.is_windows()

def test_windows_admin_install_wget():
    if wget_check.is_windows():
        wget_check.windows_admin_install_wget()

def test_install_wget():
    wget_check.install_wget()
    assert wget_check.is_wget_installed()

def test_windows_non_admin_install_wget():
    if wget_check.is_windows():
        cmd = ['choco', 'uninstall', '-y' ,'wget']
        subprocess.call(cmd)
        wget_check.windows_non_admin_install_wget()
        assert wget_check.is_wget_installed()
