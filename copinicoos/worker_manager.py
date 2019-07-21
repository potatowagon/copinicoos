import os
import logging
import sys
from multiprocessing import Process, Queue

from colorama import Fore

from .resumable import Resumable
from . import query_formatter

class WorkerManager(Resumable):
    def __init__(self, worker_list, query, total_result, download_location, polling_interval, offline_retries):
        Resumable.__init__(self)
        self.worker_list = worker_list
        self.name = "WorkerManager"
        self.query = query
        self.total_results = total_result
        self.offline_retries = offline_retries
        self.polling_interval = polling_interval
        self.download_location = download_location
        self.workdir = None
        self.logger = None

    @classmethod
    def init_from_args(self, worker_list, args):
        return self(worker_list, args.query, args.total_results, args.download_location, args.polling_interval, args.offline_retries)

    def setup_workdir(self):
        self.workdir = os.path.join(self.download_location, "copinicoos_logs")
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        self.logger = self._setup_logger()

        #create log.txt if not exist
        progress_log_path = os.path.join(self.workdir, 'WorkerManager_progress.txt')
        super().setup(progress_log_path)

        for worker in self.worker_list:
            worker.setup(self.workdir)

    def _setup_logger(self):
        # log file handler
        logger = logging.getLogger(self.name)
        logger.propagate = False
        if not logger.hasHandlers():
            f = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
            fh = logging.FileHandler(os.path.join(self.workdir, self.name + '_log.txt'))
            fh.setFormatter(f)
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)

            #log to stream handler
            sh = logging.StreamHandler(stream=sys.stdout)
            sh.setLevel(logging.DEBUG)
            logger.addHandler(sh)

        logger.setLevel(logging.DEBUG)
        return logger

    def _close_all_loggers(self):
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()

    def run_workers(self):
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
                    worker.run_in_seperate_process(worker_resume_point, ready_worker_queue)
            except Exception as e:
                print(e)
                print(Fore.RED + "Error in queueing workers")
        
        for i in range (resume_point, int(self.total_results)):
            worker = ready_worker_queue.get()
            if worker.return_msg != None:
                self.logger.info(worker.return_msg)
            p = Process(target=worker.run_in_seperate_process, args=(i, ready_worker_queue))
            p.start()
            resume_point += 1
            self.update_resume_point(resume_point)

        while not ready_worker_queue.full():
            pass
        for i in range(0, ready_worker_queue.qsize()):
            worker = ready_worker_queue.get()
            self.logger.info(worker.return_msg)
        ready_worker_queue.close()
        ready_worker_queue.join_thread()
        self._close_all_loggers()
        self.logger.info("Exiting...")

    def get_log(self):
        log_path = os.path.join(self.workdir, self.name + "_log.txt")
        return open(log_path).read()
