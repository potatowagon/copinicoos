class Resumable():
    def __init__(self):
        self.progress_log_path = None
        
    def setup(self, progress_log_path):
        self.progress_log_path = progress_log_path
        # create file if it does not exist
        progress_log = open(self.progress_log_path, 'a+')
        progress_log.close()

    def read_file(self, file_path):
        file_r = open(file_path)
        file_r.seek(0)
        out = file_r.read()
        file_r.close()
        return out

    def overwrite_file(self, file_path, msg):
        file_o = open(file_path, 'w+')
        file_o.write(msg)
        file_o.seek(0)
        file_o.close()

    def load_resume_point(self):
        try:
            resume = self.read_file(self.progress_log_path)
            if resume == '':
                resume = None
            return resume
        except:
            raise

    def update_resume_point(self, result_num):
        self.overwrite_file(self.progress_log_path, str(result_num))
