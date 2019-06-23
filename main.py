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