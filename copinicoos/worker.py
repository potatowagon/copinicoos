import os
import subprocess
import json
import time
from multiprocessing import Lock, Process
from threading import Thread
import logging 
import sys
import re
import zipfile

import colorama
from colorama import Fore, Back, Style

from .resumable import Resumable
from .loggable import Loggable

class Worker(Resumable, Loggable):
    request_lock = Lock()
    log_download_progress_lock = Lock()
    worker_instances_list = []

    def __init__(self, worker_name, username, password):
        Resumable.__init__(self)
        Loggable.__init__(self)
        self.username = username
        self.password = password
        self.name = worker_name
        self.workdir = None
        self.query = None
        self.download_location = None
        self.polling_interval = None
        self.offline_retries = None
        self.logger = None
        self.return_msg = None
        self.download_bar = None 
        self.colour = ""
        Worker.worker_instances_list.append(self)
        Worker.assign_colours()

    def __del__(self):
        try:
            Worker.worker_instances_list.remove(self)
        except ValueError as e:
            pass

    @classmethod
    def assign_colours(cls):
        '''Assign each worker instance a background colour when logging download progress'''
        for i in range(0, len(cls.worker_instances_list)):
            mode = i % 6
            if mode == 0:
                cls.worker_instances_list[i].colour = Back.CYAN + Style.BRIGHT
            elif mode == 1:
                cls.worker_instances_list[i].colour = Back.MAGENTA + Style.BRIGHT
            elif mode == 2:
                cls.worker_instances_list[i].colour = Back.BLUE + Style.BRIGHT
            elif mode == 3:
                cls.worker_instances_list[i].colour = Back.GREEN + Style.BRIGHT
            elif mode == 4:
                cls.worker_instances_list[i].colour = Back.YELLOW + Style.BRIGHT + Fore.RED
            elif mode == 5:
                cls.worker_instances_list[i].colour = Back.RED + Style.BRIGHT

    def setup(self, workdir):
        self.workdir = workdir
        self.logger = self._setup_logger(self.name, self.workdir)
        progress_log_path = os.path.join(self.workdir, self.name + '_progress.txt')
        self._setup_progress_log(progress_log_path)

    def query_total_results(self, query):
        ''' Get the total number of products in a search query 
        Args: 
            query (str): a query that request a response in json
        Returns: 
            total_results (int): the total number of product results from the query response
        '''
        json_file = "res.json"
        try:
            cmd = ["wget", "--no-check-certificate", "--user=" + self.username, "--password=" + self.password, "-O", json_file, query]
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
        query = self.query + str(result_num) 
        self.logger.debug(query)
        json_file = self.name + "_res.json"
        try:
            cmd = ["wget", "--no-check-certificate", "--user=" + self.username, "--password=" + self.password, "-O", json_file, query]
            subprocess.call(cmd)
            res_json = json.load(open(json_file))
            title = str(res_json["feed"]["entry"]["title"])
            product_uri = str(res_json["feed"]["entry"]["link"][0]["href"])
            os.remove(json_file)
            return title, product_uri
        except Exception as e:
            raise
    
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
        '''Download product in a non blocking wget subprocess
        
        Args: 
            file_path (str): path to file where downloaded content will be written to, eg ./product.zip
            product_uri (str): eg. https://scihub.copernicus.eu/dhus/odata/v1/Products('bc8421bd-2930-48eb-9caf-7b8d23df36eb')/$value

        Return:
            proc (subprocess.Popen): a Popen object that is runnng the download process
        '''
        try:
            cmd = ["wget", "-O", file_path, "--continue", "--user=" + self.username, "--password=" + self.password, product_uri]
            proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True, universal_newlines=True)
            return proc
        except Exception as e:
            raise

    def _log_download_progress(self, proc, title, file_size):
        '''logs the the relevant info of a wget download process

        Args:
            proc (subprocess.Popen): Popen object running wget download process, with stderr piped to stdout
            title (str): name of downloaded file
            file_size (int): full size of file to be downloaded
        '''
        while proc.poll() is None:
            line = proc.stdout.readline()
            if line:
                msg = None
                try:
                    response = re.search(r'HTTP request sent, awaiting response... .+', line).group(0)
                    msg = title + ", " + response
                except AttributeError as e:
                    pass
                try:
                    progress_perc = r'\d+%'
                    progress_perc = re.search(progress_perc, line).group(0)
                    time_left = r'(\d+[hms])+'
                    time_left = re.search(time_left, line).group(0)
                    downloaded = r'\d+[KM]'
                    downloaded = re.search(downloaded, line).group(0)
                    msg = title + ', Progress: ' + progress_perc + ', Downloaded: ' + downloaded + '/' + str(file_size) + ', Time left: ' + time_left 
                except AttributeError as e:
                    pass
                if msg:
                    self.log_download_progress_lock.acquire()
                    self.logger.info(self.colour + msg)
                    self.log_download_progress_lock.release()
            else:
                proc.stdout.flush()

    def query_product_size(self, product_uri):
        ''' Query the file size of product
        Args:
            product uri (str): eg. https://scihub.copernicus.eu/dhus/odata/v1/Products('23759763-91e8-4336-a50a-a143e14c8d69')/$value
        Returns:
            product file size in bytes (int) or None if product_uri query failed
        '''
        try:
            cmd = ["wget", "--spider", "--user=" + self.username, "--password=" + self.password, product_uri]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            m = re.search(r'(?<=Length: )\d+', str(out))
            length = int(m.group(0))
            return length
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Error in querying product size for " + product_uri)
            return None

    def get_downloaded_product_size(self, file_path):
        try:
            b = os.path.getsize(file_path)
            return int(b)
        except Exception as e:
            self.logger.error(e)

    def _hold_lock(self, request_lock):
        self.logger = self._setup_logger(self.name, self.workdir)
        self.logger.debug("\n\n" + self.name + " has the lock. Ready to send requests...\n\n")
        time.sleep(5)
        request_lock.release()

    def _prepare_to_request(self):
        ''' prepare to send a request by acquiring lock. 
        Has 5 seconds to be the only one making a request while holding lock
        '''
        self.request_lock.acquire()
        hold_lock_thread = Thread(target=self._hold_lock, args=(self.request_lock,))
        hold_lock_thread.start()
        
    def register_settings(self, query, download_location, polling_interval, offline_retries):
        self.query = query
        self.download_location = download_location
        self.polling_interval = polling_interval
        self.offline_retries = offline_retries

    def _is_bad_zipfile(self, file_path):
        try:
            with zipfile.ZipFile(file_path) as zf:
                zf.close()
            return False
        except zipfile.BadZipFile as e:
            self.logger.error(file_path + " could not be opened.")
            return True
        except Exception as e:
            self.logger.error(e)            

    def run(self, result_num, uri_query_max_retries=3):
        status = None
        title, product_uri = self.query_product_uri_with_retries(result_num)
        file_path = os.path.join(self.download_location, title + ".zip")
        complete_product_size = self.query_product_size(product_uri)
        max_attempts = self.offline_retries + 1
        for attempt in range(1, self.offline_retries + 2):
            self.logger.info("Download attempt number " + str(attempt) + " of " + str(max_attempts))
            self._prepare_to_request()
            self.logger.info(Fore.GREEN + "Begin downloading\n" + title + "\nat\n" + product_uri + "\n")
            proc = self.download_product(file_path, product_uri)
            self._log_download_progress(proc, title, complete_product_size)
            product_size = self.get_downloaded_product_size(file_path)
            if product_size == 0:
                self.logger.warning(Fore.YELLOW + "Product could be offline. Retrying after " + str(self.polling_interval) + " seconds.")
                status = "OFFLINE"
                time.sleep(self.polling_interval)
            elif product_size < complete_product_size:
                self.logger.warning(Fore.YELLOW + "There was a break in connection.")
                status = "FAILED"
            else:
                if self._is_bad_zipfile(file_path):
                    self.logger.error("Product download failed.")
                    status = "FAILED"
                else:
                    self.logger.info(Fore.GREEN + "Downloaded product " + title)
                    status = "SUCCESS"
                break
        outcome = "ResultNum=" + str(result_num) + " " + self.name + " " + title + " " + status
        self.logger.info(outcome)
        return outcome

    def run_in_seperate_process(self, result_num, ready_worker_queue, request_lock, log_download_progress_lock):
        # Setting up logger again because logger is shallow copied to new process and looses setup
        self.logger = self._setup_logger(self.name, self.workdir)
        self.request_lock = request_lock
        self.log_download_progress_lock = log_download_progress_lock
        self.return_msg = None
        self.update_resume_point(result_num)
        self.logger.info("running worker" + self.name)
        self.return_msg = self.run(result_num)
        self._close_all_loggers()
        self.request_lock = None
        self.log_download_progress_lock = None
        ready_worker_queue.put(self)