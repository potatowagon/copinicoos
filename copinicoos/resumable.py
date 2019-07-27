class Resumable():
    '''Enables a resume point'''
    def __init__(self):
        self.progress_log_path = None
        
    def _setup_progress_log(self, progress_log_path):
        '''Setup the progress log to store the resume point. 

        Args:
            progress_log_path (str): the path to the progress log file 
        '''
        self.progress_log_path = progress_log_path
        # create file if it does not exist
        progress_log = open(self.progress_log_path, 'a+')
        progress_log.close()

    def __read_file(self, file_path):
        '''Reads contents of a file

        Returns:
            out (str): the contents of the file as a str
        '''
        file_r = open(file_path)
        file_r.seek(0)
        out = file_r.read()
        file_r.close()
        return out

    def __overwrite_file(self, file_path, msg):
        '''Overwrites text of a file from the start of file

        Args:
            file_path (str): the file pathof file to be overwritten
            msg (str): message to write to file
        '''
        file_o = open(file_path, 'w+')
        file_o.write(str(msg))
        file_o.seek(0)
        file_o.close()

    def load_resume_point(self):
        '''Loads resume point

        Returns:
            The resume point (int) or None progress log is empty, meaning a fresh run
        '''
        try:
            resume = self.__read_file(self.progress_log_path)
            if resume == '':
                return None
            return int(resume)
        except:
            raise

    def update_resume_point(self, result_num):
        '''Updates resume point

        Args:
            result_num (int): the product index in relation to the query, starting from 0
        '''
        self.__overwrite_file(self.progress_log_path, str(result_num))
