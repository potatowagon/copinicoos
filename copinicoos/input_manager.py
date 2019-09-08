import os
import subprocess
import json
import argparse
import shutil
import getpass

from colorama import Fore

from .worker import Worker
from . import query_formatter
from .account_manager import AccountManager
from . import secure

class InputManager():
    '''This class is repsonsible for collecting input from user and parsing it as auguments for WorkerManager to consume'''
    def __init__(self):
        self.args = Args()
        self.account_manager = AccountManager()
        self.args.download_location = os.getcwd()
        self.args.polling_interval = 1800 # every 30 mins
        self.args.offline_retries = 24 # give half day's grace for product to be online
        self.config_path = None
        self.copinicoos_logs_path = None

    def interactive_input(self):
        refresh = True
        self._get_download_location_input_i()
        if self._config_exists() and self._prompt_resume():
            try:
                self._load_from_config()
                refresh = False
            except Exception as e:
                print(Fore.RED + str(e))
                refresh = True
        if refresh:      
            self._delete_savepoint()
            self._get_account_input_i()
            self._get_query_input_i()
        self._get_polling_interval_input_i()
        self._get_offline_retries_input_i()
    
    def _get_account_input_i(self):
        print(Fore.YELLOW + "Enter number of accounts: ")
        total_accounts = None
        while total_accounts == None:
            try:
                total_accounts = int(input())
            except ValueError as e:
                print(Fore.RED + "Invalid input. Please enter an integer.")
        i = 1
        while i <= total_accounts:
            print(Fore.YELLOW + "Enter username of account " + str(i))
            username = input()
            print(Fore.YELLOW + "Enter password of account " + str(i))
            password = getpass.getpass()
            if self.account_manager.add_two_workers_per_account(username, password):
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
        self._set_download_location(download_location)

    def _set_download_location(self, download_location):
        '''Checks of path to download location is valid before setting the download location. Also sets the config file path'''
        if os.path.exists(download_location):
            self.args.download_location = download_location
            print("Download path set to " + download_location)
        else: 
            print("Using default path.")
        self.copinicoos_logs_path = os.path.join(self.args.download_location, "copinicoos_logs")
        self.config_path = os.path.join(self.copinicoos_logs_path, "config.json")

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
        '''Uses account manager to check that there is at list one worker initialised before returning worker_list
        
        Returns: 
            worker_list if check passed
        '''
        return self.account_manager.return_worker_list()
    
    def return_args(self):
        '''Checks that all required args have been initialised
        
        Returns: 
            arguments (Args): Args object if check pass
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
        # create global options parser
        parser_global_options = argparse.ArgumentParser(add_help=False)
        parser_global_options.add_argument('-d', '--download-location', type=str, help="Path to download folder", default=self.args.download_location)
        parser_global_options.add_argument('-r', '--offline-retries', type=int, help="Number of get retries for offline product", default=self.args.offline_retries)
        parser_global_options.add_argument('-p', '--polling-interval', type=int, help="Duration between each offline retry, in seconds", default=self.args.polling_interval)

        description = Fore.GREEN + 'Coopinicoos is a Copernicus Download Manager.\n\n' + Fore.YELLOW + 'Run without aruguments to launch interactive mode.'
        epilog = Fore.GREEN + 'Originally written by Wong Wen Qi Sherry <e0007652@u.nus.edu>.\nPlease send bug reports to <https://github.com/potatowagon/copinicoos/issues>.\n\nSource code and docs in <https://github.com/potatowagon/copinicoos>.\nHomepage: <https://potatowagon.github.io/copinicoos/>.\n\nLicensed under the terms of the MIT license. Please see <https://github.com/potatowagon/copinicoos/blob/master/LICENSE>.'

        # create the top-level parser
        parser = argparse.ArgumentParser(prog='copinicoos', description=description, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
        subparsers = parser.add_subparsers(help='sub-command help', dest='subcmd')
        
        # create the parser for the "resume" command
        parser_resume = subparsers.add_parser('resume', help='Resume downloading from last savepoint', parents=[parser_global_options])

        # create the parser for the "fresh" command
        parser_fresh = subparsers.add_parser('fresh', fromfile_prefix_chars='@', help='Start a fresh download', parents=[parser_global_options])
        parser_fresh.add_argument('query', type=str, help="The query in OpenSearch API format. Input path to @query.txt or input query as string directly. To generate a query, in Copenicus Open Hub apply search filters and search. The query will appear below the search bae as Request Done: (...)")
        parser_fresh.add_argument('credentials', type=str, help="Input path to @example.json file with credentials, or input credentials in json format.\nThe username is abbr. with uN, password with pN, where N is the account number, starting from one. for eg.\n{'u1':'username1','p1':'password1','u2':'username2','p2':'password2'}\nAttempts a login with 2 accounts")  
        
        if test_args == None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(test_args)

        self._set_download_location(args.download_location)
        self.args.offline_retries = args.offline_retries
        self.args.polling_interval = args.polling_interval
        if args.subcmd == 'resume':
            self._load_from_config()
        elif args.subcmd == 'fresh':
            json_creds = self.get_json_creds(args.credentials)
            self.account_manager.add_workers_from_json_creds(json_creds)
            self.get_total_results_from_query(args.query)
            self.args.query = query_formatter.req_search_res_json(args.query)
        
    def get_json_creds(self, arg):
        if arg.endswith(".json"):
            return json.load(open(arg))
        arg = arg.strip()
        arg = arg.replace('\n', '')
        arg = arg.replace(' ', '')
        return json.loads(arg)

    def get_total_results_from_query(self, query):
        query = query_formatter.req_search_res_json(query)
        print("\nSending query: " + query + "\n")
        try:
            self.args.total_results = self.return_worker_list()[0].query_total_results(query)
        except Exception as e:
            print(e)
            print(Fore.RED + "Query failed. Please check query and try again")
        return self.args.total_results

    def _config_exists(self):
        return os.path.exists(self.config_path)

    def _prompt_resume(self):
        while True:
            print(Fore.YELLOW + "Save point found. Resume previous download? (y/n)")
            ans = input()
            if ans == "y" or ans == "yes" or ans == "Y" or ans == "YES" or ans == "Yes":
                return True
            elif ans == "n" or ans == "no" or ans == "N" or ans == "NO" or ans == "No":
                return False
            else:
                print(Fore.RED + "Invalid input. Try again")
    
    def _load_from_config(self):
        '''load total results, query, and workers from config'''
        try:
            config_dict = json.load(open(self.config_path))
            for key in config_dict:
                if key != "query":
                    name = key
                    creds = config_dict[name]
                    username = creds["username"]
                    password = secure.decrypt(creds["username"], creds["password"])
                    self.account_manager.add_worker(name, username, password)
            query = config_dict["query"]
            self.get_total_results_from_query(query)
            print(Fore.GREEN + str(self.args.total_results) + " products found.")
            if self.args.total_results == None:
                raise Exception("Failed to query total results.")     
            self.args.query = query
        except Exception as e:
            self.account_manager.worker_list = []
            raise Exception("Failed to load config from config.json")
        
    def _delete_savepoint(self):
        if os.path.exists(self.copinicoos_logs_path):
            shutil.rmtree(self.copinicoos_logs_path)

class Args():
    '''Required args interface'''
    def __init__(self):
        self.query = None
        self.total_results = None
        self.download_location = None
        self.offline_retries = None
        self.polling_interval = None
