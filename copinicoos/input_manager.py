import os
import subprocess
import json
import argparse

from colorama import Fore

from .worker import Worker
from . import query_formatter

class InputManager():
    def __init__(self):
        self.args = Args()
        self.worker_list = []
        self.args.download_location = os.getcwd()
        self.args.polling_interval = 6
        self.args.offline_retries = 2

    @staticmethod
    def is_worker_auth_valid(username, password):
        '''
        Send sample query to check worker auth
        returns: True if valid
        '''
        print("Authenticationg worker...")
        json_file = "res.json"
        sample_query = "https://scihub.copernicus.eu/dhus/search?q=*&rows=1&format=json"
        try:
            cmd = "wget --no-check-certificate --user=" + username + " --password=" + password + " -O " + json_file + " " + sample_query
            subprocess.call(cmd)
            res_json = json.load(open(json_file))
            if res_json["feed"] is not None:
                os.remove(json_file)
                return True
        except Exception as e:
            print(e)
            return False

    def is_unique_worker_cred(self, username, password):
        '''
        Check if username and password have already been used to initialise a worker
        returns: True if unused 
        '''
        for worker in self.worker_list:
            if username == worker.username:
                return False
        return True

    def interactive_input(self):
        self._get_worker_input_i()
        self._get_query_input_i()
        self._get_download_location_input_i()
        self._get_polling_interval_input_i()
        self._get_offline_retries_input_i()
    
    def _get_worker_input_i(self):
        print(Fore.YELLOW + "Enter number of workers: ")
        total_workers = int(input())
        i = 1
        while i <= total_workers:
            print(Fore.YELLOW + "Enter username of worker " + str(i))
            username = input()
            print(Fore.YELLOW + "Enter password of worker " + str(i))
            password = input()
            if self.add_worker(username, password):
                i += 1
                
    def _get_query_input_i(self):
        print(Fore.YELLOW + "Enter query: ")
        while self.args.total_results is None:
            query = input()
            self.args.total_results = self.get_total_results_from_query(query)
        print(Fore.GREEN + str(self.args.total_results) + " products found.")
        self.args.query = query_formatter.req_search_res_json(query)

    def _get_download_location_input_i(self):
        print(Fore.YELLOW + "Default download directory set to " + self.args.download_location + "\nEnter new path to change, if not will use default.")
        download_location = str(input())
        if os.path.exists(download_location):
            self.args.download_location = download_location
            print("Download path set to " + download_location)
        else: 
            print("Using default path.")

    def _get_polling_interval_input_i(self):
        print(Fore.YELLOW + "Default polling interval for offline products set to " + str(self.args.polling_interval) + " seconds.\nEnter new polling interval, if not will use default.")
        try:
            polling_interval = int(input())
            self.args.polling_interval = polling_interval
            print("Polling interval set to " + str(self.args.polling_interval) + " seconds.")
        except Exception as e:
            print(e)
            print("Using default polling interval.")

    def _get_offline_retries_input_i(self):
        print(Fore.YELLOW + "Default offline retries is set to " + str(self.args.offline_retries) + "\nEnter new offline retries, if not will use default.")
        try:
            offline_retries = int(input())
            self.args.offline_retries = offline_retries
            print("Offline retries set to " + str(self.args.offline_retries))
        except Exception as e:
            print(e)
            print("Using default offline retries.")

    def return_worker_list(self):
        '''
        Checks that there is at list one worker initialised before returning worker_list
        returns: worker_list if check passed
        '''
        try:
            int(len(self.worker_list))
            return self.worker_list
        except Exception as e:
            print(e)
            print(Fore.RED + "Error in returning workers. No workers initialised.")
    
    def return_args(self):
        '''
        Checks that all required args have been initialised
        return: Args if check passed
        '''
        try:
            for arg in Args().__dict__:
                if self.args.__dict__[arg] is None:
                    raise Exception(arg + " is not defined.")
            return self.args
        except Exception as e:
            print(e)
            print(Fore.RED + "Error in input. One or more required argument is not defined.")

    def cmd_input(self, test_args=None):
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@', description="Copernicus Downloader Bot. Use @ to load input from file.\neg. py -m copinicoos '( (platformname:Sentinel-1 AND filename:S1A_*))' {'u1':'username1','p1':'password1','u2':'username2','p2':'password2'}")
        parser.add_argument('query', type=str, help="The query in OpenSearch API format. To generate a query, in Copenicus Open Hub apply search filters and search. The query will appear below the search bae as Request Done: (...)")
        parser.add_argument('credentials', type=str, help="Input path to @example.json file with credentials, or input credentials in json format.\nThe username is abbr. with uN, password with pN, where N is the account number, starting from one. for eg.\n{'u1':'username1','p1':'password1','u2':'username2','p2':'password2'}\nAttempts a login with 2 accounts")
        parser.add_argument('-d', '--download-location', help="Path to download folder", default=self.args.download_location)
        parser.add_argument('-r', '--offline-retries', help="Number of get retries for offline product", default=self.args.offline_retries)
        parser.add_argument('-p', '--polling-interval', help="Duration between each offline retry, in seconds", default=self.args.polling_interval)
        if test_args == None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(test_args)
        if args != None:
            json_creds = self.get_json_creds(args.credentials)
            self.add_workers_from_json_creds(json_creds)
            self.get_total_results_from_query(args.query)
            self.args.query = query_formatter.req_search_res_json(args.query)
            self.args.download_location = args.download_location
            self.args.offline_retries = args.offline_retries
            self.args.polling_interval = args.polling_interval
        
    def get_json_creds(self, arg):
        if arg.endswith(".json"):
            return json.load(open(arg))
        arg = arg.strip()
        arg = arg.replace('\n', '')
        arg = arg.replace(' ', '')
        return json.loads(arg)

    def add_workers_from_json_creds(self, json_creds):
        for k in json_creds:
            if k.startswith("u"):
                username = json_creds[k]
                try:
                    password = json_creds["p" + k[1:]]
                except Exception as e:
                    print(e)
                    print(Fore.RED + "Password not set for " + username)
                if not self.add_worker(username, password):
                    raise Exception("Failed to add worker for username: " + username)

    def add_worker(self, username, password):
        ''' Creates and adds a Worker to worker list.
        returns True if successful, else returns False
        '''
        if not InputManager().is_worker_auth_valid(username, password):
            print(Fore.RED + "Authentication failed, please try again.")
            return False
    
        if self.is_unique_worker_cred(username, password):
            self.worker_list.append(Worker(username, password))
            print(Fore.GREEN + "Worker sucessfully authenticated.")
            return True
        else:
            print(Fore.RED + "Credentials already used. Please try again.")
            return False

    def get_total_results_from_query(self, query):
        query = query_formatter.req_search_res_json(query)
        print("\nSending query: " + query + "\n")
        try:
            self.args.total_results = self.return_worker_list()[0].query_total_results(query)
        except Exception as e:
            print(e)
            print(Fore.RED + "Query failed. Please check query and try again")
        return self.args.total_results

class Args():
    '''
    Required args interface
    '''
    def __init__(self):
        self.query = None
        self.total_results = None
        self.download_location = None
        self.offline_retries = None
        self.polling_interval = None
