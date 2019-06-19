import os  # os.sep
import sys  # sys.exit
import subprocess
from threading import Thread
from multiprocessing import Process
from multiprocessing import Lock
import re
import time
import json
import colorama
from colorama import Fore
import asyncio


colorama.init(convert=True, autoreset=True)

class Resumable():
    def __init__(self):
        self.progress_log_path = None
        
    def setup(self, progress_log_path):
        self.progress_log_path = progress_log_path
        # create file if it does not exist
        progress_log = open(self.progress_log_path, 'a+')
        progress_log.close()

    def read_file(self, file_path):
        file_r = open(file_path)
        file_r.seek(0)
        out = file_r.read()
        file_r.close()
        return out

    def overwrite_file(self, file_path, msg):
        file_o = open(file_path, 'w+')
        file_o.write(msg)
        file_o.seek(0)
        file_o.close()

    def load_resume_point(self):
        try:
            resume = self.read_file(self.progress_log_path)
            if resume == '':
                resume = None
            return resume
        except:
            raise

    def update_resume_point(self, result_num):
        self.overwrite_file(self.progress_log_path, str(result_num))

class Worker(Resumable):
    request_lock = Lock()

    def __init__(self, username, password):
        Resumable.__init__(self)
        self.username = username
        self.password = password
        self.name = username
        self.workdir = None
        self.query = None
        self.download_location = None
        self.polling_interval = None
        self.offline_retries = None
        self.worker_log = None
    
    def set_name(self, name):
        self.name = name

    def setup(self, workdir):
        self.workdir = workdir
        # create log files if not exist
        self.worker_log = open(os.path.join(self.workdir, self.name + '_log.txt'), 'w+')
        progress_log_path = os.path.join(self.workdir, self.name + '_progress.txt')
        super().setup(progress_log_path)

    def query_total_results(self, query):
        '''
        params: a query that request a response in json
        returns: the total number of product results from the query response
        '''
        json_file = "res.json"
        try:
            cmd = "wget --no-check-certificate --user=" + self.username + " --password=" + self.password + " -O " + json_file + " " + query
            subprocess.call(cmd)
            res_json = json.load(open(json_file))
            total_results = int(res_json["feed"]["opensearch:totalResults"])
            if total_results <= 0:
                raise ValueError
            os.remove(json_file)
            return total_results
        except Exception as e:
            raise

    def query_product_uri(self, result_num):
        '''
        params: result number
        returns: title and product_uri, eg. "S1A_IW_GRDH_1SDV_20181011T115601_20181011T115626_024088_02A208_C886", "https://scihub.copernicus.eu/dhus/odata/v1/Products('7bc7da0c-8241-4bbe-8d59-1661667c6161')/$value"
        '''
        query = self.query + str(result_num) + '"'
        print(query)
        json_file = self.name + "_res.json"
        try:
            cmd = "wget --no-check-certificate --user=" + self.username + " --password=" + self.password + " -O " + json_file + " " + query
            subprocess.call(cmd)
            res_json = json.load(open(json_file))
            title = str(res_json["feed"]["entry"]["title"])
            product_uri = str(res_json["feed"]["entry"]["link"][0]["href"])
            product_uri = self.format_product_uri(product_uri)
            return title, product_uri
        except Exception as e:
            raise

    def format_product_uri(self, product_uri):
        product_uri = '"' + product_uri + '"'
        return product_uri
    
    def query_product_uri_with_retries(self, result_number, max_retries=3):
        title = None
        product_uri = None
        uri_query_retries = 0
        uri_query_max_retries = max_retries
        while uri_query_retries <= uri_query_max_retries and (title is None or product_uri is None):
            try:
                title, product_uri = self.query_product_uri(result_number)
            except Exception as e:
                print(e)
                print(Fore.RED + "Error in querying product uri from result number.")
                print("Retrying " + str(uri_query_retries) + " out of " + str(uri_query_max_retries) + " times.")
                uri_query_retries += 1
        return title, product_uri

    def download_product(self, file_path, product_uri):
        try:
            cmd = "wget -O " + file_path + " --continue --user=" + self.username + " --password="+ self.password + " " + product_uri
            print(Fore.YELLOW + cmd)
            subprocess.call(cmd)
        except Exception as e:
            raise
        '''
        self.process = Process(target=None)
        self.process.start()
        '''

    def download_began(self, file_path):
        try:
            b = os.path.getsize(file_path)
        except Exception as e:
            print(e)
            return False
        if b > 0:
            return True
        else:
            return False

    def download(self, result_num):
        '''
        self.update_resume_point(result_num)
        self._prepare_to_request()
        product_uri = self.query_product_uri(result_num)
        self._prepare_to_request()
        download_status = self.download(product_uri)
        i = 0
        while download_status != "success" and i < self.offline_retries:
            #sleep
            #download
            pass
        #update worker log
        ready_worker_queue.put_nowait(self)
        return download_status
        '''
        pass

    def _hold_lock(self):
        print(self.name + " has the lock. Ready to send requests...")
        time.sleep(5)
        self.request_lock.release()

    def _prepare_to_request(self):
        ''' prepare to send a request by acquiring lock. 
        Has 5 seconds to be the only one making a request while holding lock
        '''
        self.request_lock.acquire()
        hold_lock_thread = Thread(target=self._hold_lock)
        hold_lock_thread.start()

    def register_settings(self, query, download_location, polling_interval, offline_retries):
        self.query = query
        self.download_location = download_location
        self.polling_interval = polling_interval
        self.offline_retries = offline_retries

    def run(self, result_num, uri_query_max_retries=3):
        title, product_uri = self.query_product_uri_with_retries(result_num)
        print(Fore.GREEN + "Begin downloading\n" + title + "\nat\n" + product_uri + "\n")
        file_path = os.path.join(self.download_location, title + ".zip")
        self.download_product(file_path, product_uri)
        if not self.download_began(file_path):
            print(Fore.YELLOW + "Product could be offline. Retrying after " + str(self.polling_interval) + " seconds.")
            for i in range(1, self.offline_retries + 1):
                time.sleep(self.polling_interval)
                self.download_product(file_path, product_uri)
                if self.download_began(file_path):
                    break
            if i == self.offline_retries:
                print(Fore.RED + "Failed to download " + title + ". Moving on to next product.")

        
    def run_in_seperate_process(self, result_num, ready_worker_queue):
        self.update_resume_point(result_num)
        print("running worker", self.name)
        self.run(result_num)
        time.sleep(5)
        ready_worker_queue.put_nowait(self)
        return "success"
        
    def run_worker(self):
        for page in range(int(self.resume), int(self.total_results) + 1):
            self.overwrite_file(self.workdir + '/progress.txt', str(page))

            self.request_lock.acquire()
            hold_lock_thread = Thread(target=self._hold_lock)
            hold_lock_thread.start()

            cmd = self.workdir + '/dhusget.sh -u ' + str(self.username) + ' -p ' + str(self.password) + ' -T GRD -m "Sentinel-1" -c "' + str(self.lonlat) + '" -S ' + self.start_date + ' -E ' + self.end_date + ' -l 1 -P ' + str(page) + ' -o product -O ' + self.workdir + ' -w 5 -W 30 -L ' + self.workdir + '/dhusget_lock -n 4 -q ' + self.workdir + '/OSquery-result.xml -C ' + self.workdir + '/products-list.csv'
            print(cmd)
            subprocess.call(cmd, stdout=self.worker_log, stderr=self.worker_log, shell=True)

def main():
    
    # ommit './'
    dir_path_2014 = "morocco/2014"
    dir_path_2015 = "morocco/2015"
    dir_path_2016 = "morocco/2016"
    dir_path_2017 = "morocco/2017"
    '''
    worker2014 = Worker(secrets.worker1_username, secrets.worker1_password, dir_path_2014)
    worker2014.set_name("2014")
    worker2014.set_query(lonlat, start_2014, end_2014)
    worker2014.start_download()

    worker2015 = Worker(secrets.worker2_username, secrets.worker2_password, dir_path_2015)
    worker2015.set_name("2015")
    worker2015.set_query(lonlat, start_2015, end_2015)
    worker2015.start_download()

    worker2016 = Worker(secrets.worker3_username, secrets.worker3_password, dir_path_2016)
    worker2016.set_name("2016")
    worker2016.set_query(lonlat, start_2016, end_2016)
    worker2016.start_download()

    worker2017 = Worker(secrets.worker4_username, secrets.worker4_password, dir_path_2017)
    worker2017.set_name("2017")
    worker2017.set_query(lonlat, start_2017, end_2017)
    worker2017.start_download()
    '''
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
        except:
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
        
class WorkerManager(Resumable):
    def __init__(self, worker_list, query, total_result, download_location, polling_interval, offline_retries):
        Resumable.__init__(self)
        self.worker_list = worker_list
        self.query = query
        self.total_results = total_result
        self.offline_retries = offline_retries
        self.polling_interval = polling_interval
        self.download_location = download_location
        self.workdir = None

    @classmethod
    def init_from_args(self, worker_list, args):
        return self(worker_list, args.query, args.total_results, args.download_location, args.polling_interval, args.offline_retries)

    def setup_workdir(self):
        self.workdir = os.path.join(self.download_location, "copinicoos_logs")
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)

        #create log.txt if not exist
        progress_log_path = os.path.join(self.workdir, 'WorkerManager_progress.txt')
        super().setup(progress_log_path)

        for worker in self.worker_list:
            worker.setup(self.workdir)

    def adjust_query_for_specific_product(self):
        if not "&rows=1" in self.query:
            self.query = self.query[:(len(self.query)-1)] + "&rows=1" 
        if not "&start=" in self.query:
            self.query = self.query[:len(self.query)] + "&start=" 

    async def run_workers(self):
        ready_worker_queue = asyncio.Queue(maxsize=len(self.worker_list))
        resume_point = self.load_resume_point()
        if resume_point == None:
            resume_point = 0
        else:
            resume_point = int(resume_point)
        
        for worker in self.worker_list:
            worker.register_settings(self.query, self.download_location, self.polling_interval, self.offline_retries)
            try:
                worker_resume_point = worker.load_resume_point()
                if worker_resume_point == None:
                    ready_worker_queue.put_nowait(worker)
                else:
                    worker.run_in_seperate_process(worker_resume_point, ready_worker_queue)
            except Exception as e:
                print(e)
                print(Fore.RED + "Error in queueing workers")
        
        for i in range (resume_point, int(self.total_results)):
            worker = await ready_worker_queue.get()
            worker.run_in_seperate_process(i, ready_worker_queue)
            resume_point += 1
            self.update_resume_point(resume_point)

if __name__ == "__main__":
    input_manager = InputManager()
    if len(sys.argv) == 1:
        input_manager.interactive_input()
    else:
        input_manager.cmd_input()
    
    worker_manager = WorkerManager.init_from_args(input_manager.return_worker_list(), input_manager.return_args())
    worker_manager.adjust_query_for_specific_product()
    worker_manager.setup_workdir()
    asyncio.run(worker_manager.run_workers())