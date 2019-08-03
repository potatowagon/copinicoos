import logging
import sys
import os

class Loggable():
    '''This class has methods to manage the logger object of its child class instances.'''
    def __init__(self):
        self.name = None
        self.workdir = None
        self.logfile_path = None

    def _setup_logger(self, name, workdir):
        '''Sets up the logger

        Args:
            name (str): name of the class instance
            workdir (str):  path to directory where log will be placed

        Returns:
            Logger: an instance of a logger object which will log to the log file of the instance as well as to std out
        '''
        self.name = name
        self.workdir = workdir
        self.logfile_path = os.path.join(self.workdir, self.name + '.log')
        # log file handler
        logger = logging.getLogger(self.name)
        logger.propagate = False
        if not logger.hasHandlers() or not os.path.exists(self.logfile_path):
            f = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
            fh = logging.FileHandler(self.logfile_path)
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
        '''Close all file handlers belonging to all loggers associated in the current logging tree'''
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()

    def get_log(self):
        '''Get logs as str

        Returns:
            logs (str): what is written in the log file 
        '''
        log_path = self.logfile_path
        return open(log_path).read()
