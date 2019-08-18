import os
import subprocess
import json

from colorama import Fore

from .worker import Worker

class AccountManager():
    '''This class manages the initialisation of Workers from accounts'''
    def __init__(self):
        self.worker_list = []

    def _are_creds_valid(self, username, password):
        '''Send sample query to check worker auth

        Args:
            username (str): username used to log in to copernicus account
            password (str): password used to log in to copernicus account 
        
        Returns: 
            True if valid
        '''
        print("Authenticating worker...")
        json_file = "res.json"
        sample_query = "https://scihub.copernicus.eu/dhus/search?q=*&rows=1&format=json"
        try:
            cmd = ["wget", "--no-check-certificate", "--user=" + username, "--password=" + password, "-O", json_file, sample_query]
            subprocess.call(cmd)
            res_json = json.load(open(json_file))
            if res_json["feed"] is not None:
                os.remove(json_file)
                return True
        except Exception as e:
            print(e)
            return False

    def _num_workers_with_username(self, username):
        ''' Check number of workers initialised with a username

        Args:
            userame (str): Account username

        Returns:
            used_count (int): number of workers using the username
        '''
        used_count = 0
        for worker in self.worker_list:
            if username == worker.username:
                used_count += 1
        return used_count

    def add_workers_from_json_creds(self, json_creds):
        for k in json_creds:
            if k.startswith("u"):
                username = json_creds[k]
                try:
                    password = json_creds["p" + k[1:]]
                except Exception as e:
                    print(e)
                    print(Fore.RED + "Password not set for " + username)
                if not self.add_two_workers_per_account(username, password):
                    raise Exception("Failed to add workers for username: " + username)

    def add_two_workers_per_account(self, username, password):
        ''' Creates and adds a Worker to worker list.
        returns True if successful, else returns False
        '''
        if not self._are_creds_valid(username, password):
            print(Fore.RED + "Authentication failed, please try again.")
            return False
        used_count = self._num_workers_with_username(username)
        if used_count == 0:
            self.worker_list.append(Worker(username + "-1", username, password))
            self.worker_list.append(Worker(username + "-2", username, password))
            print(Fore.GREEN + "Worker sucessfully authenticated.")
            return True
        elif used_count == 2:
            print(Fore.RED + "Credentials already used. Please try again.")
            return False
        else:
            print(Fore.RED + "There is an error in initialising workers. Please restart.")
            return False

    def return_worker_list(self):
        '''Checks that there is at list one worker initialised before returning worker_list
        
        Returns: 
            worker_list if check passed
        '''
        try:
            if int(len(self.worker_list)) > 0:
                return self.worker_list
            else:
                raise Exception("No workers initialised.")
        except Exception as e:
            print(e)
            print(Fore.RED + "Error in returning workers. No workers initialised.")

    def add_worker(self, name, userame, password):
        if self._are_creds_valid(userame, password):
            self.worker_list.append(Worker(name, userame, password))
            print(Fore.GREEN + "Worker sucessfully authenticated.")
        else:
            raise Exception("Failed to initialise worker.")