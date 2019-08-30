import os
import logging
import sys
from multiprocessing import Process, Queue, Lock
import json

from colorama import Fore

from .resumable import Resumable
from .loggable import Loggable
from . import query_formatter

class WorkerManager(Resumable, Loggable):
    '''
    A WorkerManager manages the execution of Workers to download products.

    Args:
        worker_list ([<Worker>, ...]): a list of Workers
        query (str): the search query
        total_result (int): the total number of results from the search query 
        download_location (str): directory path to where products will be downloaded
        polling_interval (int): the number of seconds to wait before making the next request for an offline product
        offline_retries (int): the number of retry attempts to download an offline product before giving up 
    '''
    def __init__(self, worker_list, query, total_result, download_location, polling_interval, offline_retries):
        Resumable.__init__(self)
        Loggable.__init__(self)
        self.worker_list = worker_list
        self.name = "WorkerManager"
        self.query = query
        self.total_results = int(total_result)
        self.offline_retries = offline_retries
        self.polling_interval = polling_interval
        self.download_location = download_location
        self.workdir = None
        self.logger = None

    @classmethod
    def init_from_args(self, worker_list, args):
        '''Initialise an instance of WorkerManager from the Args recieved from InputManager

        Args:
            worker_list ([<Worker>, ...]): a list of Workers
            args (Args): Args recieved from InputManager
        '''
        return self(worker_list, args.query, args.total_results, args.download_location, args.polling_interval, args.offline_retries)

    def setup_workdir(self):
        '''Sets up the folder where log files will be written to.'''
        self.workdir = os.path.join(self.download_location, "copinicoos_logs")
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        self.logger = self._setup_logger(self.name, self.workdir)

        #create log.txt if not exist
        progress_log_path = os.path.join(self.workdir, 'WorkerManager_progress.txt')
        self._setup_progress_log(progress_log_path)

        for worker in self.worker_list:
            worker.setup(self.workdir)
        self._create_config()

    def run_workers(self):
        '''Runs workers by assigning them a product index relative to the total number of products in the search query (starting from 0). 
        Checks for any resume point and continues from there. 
        Each Worker is given a product index to download, and is executed in a seperate Process. 
        Free workers are queued in process.Queue 
        '''
        # create locks
        request_lock = Lock()
        log_download_progress_lock = Lock()
        # loading resume points
        self.query = query_formatter.adjust_for_specific_product(self.query)
        ready_worker_queue = Queue(maxsize=len(self.worker_list))
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
                    p = Process(target=worker.run_in_seperate_process, args=(worker_resume_point, ready_worker_queue, request_lock, log_download_progress_lock))
                    p.start()
            except Exception as e:
                self.logger.error(e)
                self.logger.error(Fore.RED + "Error in queueing workers")
        
        # assigning workers a result number to download
        for i in range (resume_point, int(self.total_results)):
            worker = ready_worker_queue.get()
            if worker.return_msg != None:
                self.logger.info(worker.return_msg)
            p = Process(target=worker.run_in_seperate_process, args=(i, ready_worker_queue, request_lock, log_download_progress_lock))
            p.start()
            resume_point += 1
            self.update_resume_point(resume_point)

        # clearing the last batch
        for i in range(0, len(self.worker_list)):
            worker = ready_worker_queue.get()
            if worker.return_msg:
                self.logger.info(worker.return_msg)
        ready_worker_queue.close()
        ready_worker_queue.join_thread()
        self._close_all_loggers()
        self.logger.info("Exiting...")

    def _create_config(self):
        config_dict = {}
        config_dict["query"] = self.query
        for worker in self.worker_list:
            creds = {}
            creds["username"] = worker.username
            creds["password"] = worker.password
            config_dict[worker.name] = creds
            with open(os.path.join(self.workdir, 'config.json'), 'w') as config_json:
                json.dump(config_dict, config_json)
        


    