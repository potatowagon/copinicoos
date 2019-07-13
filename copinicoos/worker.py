import os
import subprocess
import json
import time
from multiprocessing import Lock
from threading import Thread

import colorama
from colorama import Fore

from .resumable import Resumable

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
        self.worker_log.close()
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
            os.remove(json_file)
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
