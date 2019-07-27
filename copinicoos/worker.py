import os
import subprocess
import json
import time
from multiprocessing import Lock
from threading import Thread
import logging 
import sys

import colorama
from colorama import Fore

from .resumable import Resumable
from .loggable import Loggable

class Worker(Resumable, Loggable):
    request_lock = Lock()

    def __init__(self, username, password):
        Resumable.__init__(self)
        Loggable.__init__(self)
        self.username = username
        self.password = password
        self.name = username
        self.workdir = None
        self.query = None
        self.download_location = None
        self.polling_interval = None
        self.offline_retries = None
        self.logger = None
        self.return_msg = None 
    
    def set_name(self, name):
        self.name = name

    def setup(self, workdir):
        self.workdir = workdir
        self.logger = self._setup_logger(self.name, self.workdir)
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
        self.logger.debug(query)
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
                self._prepare_to_request()
                title, product_uri = self.query_product_uri(result_number)
            except Exception as e:
                self.logger.error(e)
                self.logger.error(Fore.RED + "Error in querying product uri from result number.")
                self.logger.error("Retrying " + str(uri_query_retries) + " out of " + str(uri_query_max_retries) + " times.")
                uri_query_retries += 1
        return title, product_uri

    def download_product(self, file_path, product_uri):
        try:
            cmd = "wget -O " + file_path + " --continue --user=" + self.username + " --password="+ self.password + " " + product_uri
            self.logger.info(Fore.YELLOW + cmd)
            subprocess.call(cmd)
        except Exception as e:
            raise
      
    def download_began(self, file_path):
        try:
            b = os.path.getsize(file_path)
        except Exception as e:
            self.logger.error(e)
            return False
        if b > 0:
            return True
        else:
            return False

    def _hold_lock(self):
        self.logger = self._setup_logger(self.name, self.workdir)
        self.logger.debug(self.name + " has the lock. Ready to send requests...")
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
        status = None
        title, product_uri = self.query_product_uri_with_retries(result_num)
        file_path = os.path.join(self.download_location, title + ".zip")
        self._prepare_to_request()
        self.logger.info(Fore.GREEN + "Begin downloading\n" + title + "\nat\n" + product_uri + "\n")
        self.download_product(file_path, product_uri)
        if not self.download_began(file_path):
            self.logger.warning(Fore.YELLOW + "Product could be offline. Retrying after " + str(self.polling_interval) + " seconds.")
            for i in range(1, self.offline_retries + 1):
                time.sleep(self.polling_interval)
                self._prepare_to_request()
                self.logger.info(Fore.GREEN + "Retry attempt " + str(i) + " of " + str(self.offline_retries))
                self.logger.info(Fore.GREEN + "Begin downloading\n" + title + "\nat\n" + product_uri + "\n")
                self.download_product(file_path, product_uri)
                if self.download_began(file_path):
                    self.logger.info(Fore.GREEN + "Downloaded product " + title)
                    status = "SUCCESS"
                    break
                else:
                    if i < self.offline_retries:
                        self.logger.info(Fore.YELLOW + "Product could be offline. Retrying after " + str(self.polling_interval) + " seconds.")
            if i == self.offline_retries:
                self.logger.info(Fore.YELLOW + "Product could be offline.")
                self.logger.info(Fore.RED + "Failed to download " + title + ". Moving on to next product.")
                status = "FAILED"
        else:
            self.logger.info(Fore.GREEN + "Downloaded product " + title)
            status = "SUCCESS"
        return self.name + " " + title + " " + status
        

    def run_in_seperate_process(self, result_num, ready_worker_queue):
        # Setting up logger again because logger is shallow copied to new process and looses setup
        self.logger = self._setup_logger(self.name, self.workdir)
        self.return_msg = None
        self.update_resume_point(result_num)
        self.logger.info("running worker" + self.name)
        self.return_msg = self.run(result_num)
        self._close_all_loggers()
        ready_worker_queue.put(self)