import subprocess
import platform
import os

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

def windows_admin_install_wget():
    print(Fore.YELLOW + "Attempting to install wget via choco.")
    if not is_choco_installed():
        install_choco()
        cmd = ["choco", "install", "wget"]
        subprocess.call(cmd)

def windows_non_admin_install_wget():
    print(Fore.YELLOW + "Attempting a non-admin install of wget.")
    # get the dir path to pip
    cmd = ["where", "pip"]
    out = subprocess.check_output(cmd).decode()
    py_script_path = os.path.dirname(out)
    arch = int(platform.architecture()[0][:2]) 
    launch_powershell_cmd = '@"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command '
    download_cmd = "\"(New-Object System.Net.WebClient).DownloadFile('https://eternallybored.org/misc/wget/1.20.3/" + str(arch) + "/wget.exe', " + "'" + os.path.join(py_script_path, 'wget.exe') + "'" + ")\""
    cmd = launch_powershell_cmd + download_cmd
    print(cmd)
    subprocess.call(cmd, shell=True)

def install_wget():
    print(Fore.YELLOW + "Copinicoos uses wget to download, and shall now attempt to install wget. If installation fails, please install wget yourself.")
    if is_windows():
        windows_non_admin_install_wget()
        if not is_wget_installed():
            print(Fore.RED + "Non admin install of wget failed.")
            windows_admin_install_wget()
    elif is_macos():
        cmd = ["brew", "install", "wget"]
        subprocess.call(cmd)
    elif is_linux():
        cmd = ["apt-get", "install", "wget"]
        subprocess.call(cmd)
