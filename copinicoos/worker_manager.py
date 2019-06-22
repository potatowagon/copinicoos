import os
import asyncio

from colorama import Fore

from .resumable import Resumable

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
