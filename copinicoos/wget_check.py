import subprocess
import platform

from colorama import Fore

def is_wget_installed() -> bool:
    '''Check if wget is installed by calling it through a subprocess and analysing the output

    Returns:
        is_installed (bool)
    '''
    try:
        cmd = ["wget", "--version"]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        is_installed = 'Hrvoje Niksic' in str(out)
        return is_installed
    except FileNotFoundError as e:
        return False

def is_macos() -> bool:
    system = platform.system()
    return 'Darwin' in system

def is_windows() -> bool:
    system = platform.system()
    return 'Windows' in system

def is_linux() -> bool:
    system = platform.system()
    return 'Linux' in system

def is_choco_installed() -> bool:
    try:
        cmd = ["choco", "-?"]
        out = str(subprocess.check_output(cmd, stderr=subprocess.STDOUT))
        return 'Chocolatey' in out
    except FileNotFoundError as e:
        return False

def install_choco():
    print(Fore.YELLOW + "Attempting to install chocolatey. This step requires admin rights. If this fails, try running copinicoos from an Administrative shell, or install chocolatey yourself.")
    cmd = '@\"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command \"iex ((New-Object System.Net.WebClient).DownloadString(\'https://chocolatey.org/install.ps1\'))\" && SET \"PATH=%PATH%;%ALLUSERSPROFILE%\\chocolatey\\bin'
    subprocess.call(cmd, shell=True)

def install_wget():
    print(Fore.YELLOW + "Copinicoos uses wget to download, and shall now attempt to install wget. If installation fails, please install wget yourself.")
    if is_windows():
        if not is_choco_installed():
            install_choco()
        cmd = ["choco", "install", "wget"]
        subprocess.call(cmd)
    elif is_macos():
        cmd = ["brew", "install", "wget"]
        subprocess.call(cmd)
    elif is_linux():
        cmd = ["apt-get", "install", "wget"]
        subprocess.call(cmd)
