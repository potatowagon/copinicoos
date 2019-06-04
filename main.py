import os  # os.sep
import sys  # sys.exit
import subprocess
from threading import Thread
from multiprocessing import Process
from multiprocessing import Lock
#import secrets
import re
import time
import json
import colorama
from colorama import Fore

colorama.init(convert=True, autoreset=True)

class Worker():
    request_lock = Lock()

    def __init__(self, username, password, workdir):
        self.username = username
        self.password = password
        self.workdir = workdir
        self.resume = None
        self.total_results = None
        self.name = username
        self.process = None

        self.lonlat = None
        self.start_date = None
        self.end_date = None

        self.progress_log = None
        self.worker_log = None
        self.upload_log = None
        self.is_busy = False

    def set_name(self, name):
        self.name = name

    def set_query(self, lonlat, start_date, end_date):
        self.lonlat = lonlat
        self.start_date = start_date
        self.end_date = end_date

    def set_lonlat(self, lonlat):
        self.lonlat = lonlat

    def set_start_date(self, start_date):
        self.start_date = start_date

    def set_end_date(self, end_date):
        self.end_date = end_date

    def _read_file(self, file_r):
        file_r.seek(0)
        out = file_r.read()
        file_r.close()
        return out

    def _overwrite_file(self, file_path, msg):
        file_o = open(file_path, 'w+')
        file_o.write(msg)
        file_o.seek(0)
        file_o.close()

    def setup(self):
        # create workdir
        cmd = "mkdir -p " + self.workdir
        subprocess.call(cmd, shell=True)

        #copy download script to work dir
        cmd = "cp ./dhusget.sh " + self.workdir
        subprocess.call(cmd, shell=True)
        cmd = "chmod +x " + self.workdir + "/dhusget.sh"
        subprocess.call(cmd, shell=True)

        # create log files
        self.progress_log = open(self.workdir + '/progress.txt', 'a+')
        self.worker_log = open(self.workdir + '/worker_log.txt', 'w+')
        self.upload_log = open(self.workdir + '/upload_log.txt', 'w+')

        # commit logs
        cmd = "git add --all" 
        subprocess.call(cmd, shell=True)

        # load resume point
        self.resume = self._read_file(self.progress_log)
        if self.resume == '':
            self.resume = 1

    def run_query(self):
        return None

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
            return total_results
        except Exception as e:
            raise

    def start_download(self):
        self.setup()
        self.run_query()
        self.process = Process(target=self._run_worker)
        self.process.start()

    def _hold_lock(self):
        print(self.name + " has the lock. Begin downloading...")
        time.sleep(5)
        self.request_lock.release()

    def _run_worker(self):
        for page in range(int(self.resume), int(self.total_results) + 1):
            self._overwrite_file(self.workdir + '/progress.txt', str(page))

            self.request_lock.acquire()
            hold_lock_thread = Thread(target=self._hold_lock)
            hold_lock_thread.start()

            cmd = self.workdir + '/dhusget.sh -u ' + str(self.username) + ' -p ' + str(self.password) + ' -T GRD -m "Sentinel-1" -c "' + str(self.lonlat) + '" -S ' + self.start_date + ' -E ' + self.end_date + ' -l 1 -P ' + str(page) + ' -o product -O ' + self.workdir + ' -w 5 -W 30 -L ' + self.workdir + '/dhusget_lock -n 4 -q ' + self.workdir + '/OSquery-result.xml -C ' + self.workdir + '/products-list.csv'
            print(cmd)
            subprocess.call(cmd, stdout=self.worker_log, stderr=self.worker_log, shell=True)

            new_file = self._untracked_file_name()
            print(new_file)

            cmd = "git status -s | grep '?? " + self.workdir + "' | awk '{ print $2 }' | xargs git add" 
            subprocess.call(cmd, stdout=self.worker_log, stderr=self.worker_log, shell=True)

            cmd = "git add " + self.workdir + "/progress.txt" 
            subprocess.call(cmd, stdout=self.worker_log, stderr=self.worker_log, shell=True)

            cmd = "git commit -m'add file'" 
            subprocess.call(cmd, stdout=self.worker_log, stderr=self.worker_log, shell=True)

            #thread_upload = Thread(target=self._run_upload, args=(new_file, self.upload_log))
            #thread_upload.start()

    def _run_upload(self, new_file, log):
        cmd = "git push data master" 
        subprocess.call(cmd, stdout=log, stderr=log, shell=True)

        cmd = "rm " + new_file
        subprocess.call(cmd, stdout=log, stderr=log, shell=True)

    def _untracked_file_name(self):
        cmd = "git status -s | grep '?? " + self.workdir + "' | awk '{ print $2 }'"
        return subprocess.check_output(cmd, shell=True)

def main():
    
    lonlat = "91.02953481336696,22.018870264782876:91.10092418414045,22.096923117944428" #domar char, bangladesh
    
    #YYYY-MM-DDThh:mm:ss.cccZ
    start_2014 = "2014-01-01T00:00:00.000Z"
    end_2014 = "2014-12-31T23:59:59.000Z"

    start_2015 = "2015-01-01T00:00:00.000Z"
    end_2015 = "2015-12-31T23:59:59.000Z"

    start_2016 = "2016-01-01T00:00:00.000Z"
    end_2016 = "2016-12-31T23:59:59.000Z"

    start_2017 = "2017-01-01T00:00:00.000Z"
    end_2017 = "2017-12-31T23:59:59.000Z"

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
        self.worker_list = []
        self.query = None
        self.total_results = None
        self.offline_retries = 10
        self.polling_interval = 10800
        self.download_location = os.getcwd()

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
                    self.worker_list.append(Worker(username, password, self.download_location))
                    print(Fore.GREEN + "Worker sucessfully authenticated.")
                    i += 1
                else:
                    print(Fore.RED + "Credentials already used. Please try again.")
        
        print(Fore.YELLOW + "Enter query: ")
        while self.total_results is None:
            query = input()
            query = InputManager.format_query(query)
            print("\nSending query: " + query + "\n")
            try:
                self.total_results = self.worker_list[0].query_total_results(query)
            except:
                print(Fore.RED + "Query failed. Please check query and try again")
        print(Fore.GREEN + str(self.total_results) + " products found.")

if __name__ == "__main__":
    input_manager = InputManager()
    if len(sys.argv) == 1:
        input_manager.interactive_input()
    main()