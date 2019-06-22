import os
import subprocess
import json

from colorama import Fore

from .worker import Worker

class InputManager():
    def __init__(self):
        self.args = Args()
        self.worker_list = []
        self.args.download_location = os.getcwd()
        self.args.polling_interval = 6
        self.args.offline_retries = 2

    @staticmethod
    def format_query(query):
        query = query.strip()

        request_done_str = "Request Done: "
        if query.startswith(request_done_str):
            query = query.replace(request_done_str, "")
        
        if query.startswith('"') and query.endswith('"'):
            query = query[1:len(query)-1]

        if query.startswith("'") and query.endswith("'"):
            query = query[1:len(query)-1]
        
        if not '\\"' in query:
            if '"' in query:
                query = query.replace('"', '\\"')

        query = '"https://scihub.copernicus.eu/dhus/search?q=' + query + '&format=json"'
        return query

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
            if not InputManager().is_worker_auth_valid(username, password):
                print(Fore.RED + "Authentication failed, please try again.")
            else:
                if self.is_unique_worker_cred(username, password):
                    self.worker_list.append(Worker(username, password))
                    print(Fore.GREEN + "Worker sucessfully authenticated.")
                    i += 1
                else:
                    print(Fore.RED + "Credentials already used. Please try again.")
                
    def _get_query_input_i(self):
        print(Fore.YELLOW + "Enter query: ")
        while self.args.total_results is None:
            query = input()
            query = InputManager.format_query(query)
            print("\nSending query: " + query + "\n")
            try:
                self.args.total_results = self.return_worker_list()[0].query_total_results(query)
            except:
                print(Fore.RED + "Query failed. Please check query and try again")
        print(Fore.GREEN + str(self.args.total_results) + " products found.")
        self.args.query = query

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

    def cmd_input(self):
        '''
        TODO
        '''
        pass

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
