import os  # os.sep
import sys  # sys.exit
import subprocess
from threading import Thread
import secrets
import re

def runQuery(worker_username, worker_password, lonlat, start_date, end_date, log):
    cmd = './dhusget.sh -u ' + str(worker_username) + ' -p ' + str(worker_password) + ' -T GRD -m "Sentinel-1" -c "' + str(lonlat) + '" -S ' + start_date + ' -E ' + end_date + ' -l 1 -P 1'
    subprocess.call(cmd, stdout=log, stderr=log, shell=True)

def runWorker(worker_username, worker_password, lonlat, start_date, end_date, dir_path, resume, max_results, worker_log, upload_log):
    for page in range(int(resume), int(max_results) + 1):
        overwrite_file(dir_path + '/progress.txt', str(resume))
        cmd = './dhusget.sh -u ' + str(worker_username) + ' -p ' + str(worker_password) + ' -T GRD -m "Sentinel-1" -c "' + str(lonlat) + '" -S ' + start_date + ' -E ' + end_date + ' -l 1 -P ' + str(page) + ' -o product -O ' + dir_path + ' -w 5 -W 30'
        print(cmd)
        subprocess.call(cmd, stdout=worker_log, stderr=worker_log, shell=True)

        new_file = untracked_file_name(dir_path)
        print(new_file)

        cmd = "git status -s | grep '?? " + dir_path + "' | awk '{ print $2 }' | xargs git add" 
        subprocess.call(cmd, stdout=worker_log, stderr=worker_log, shell=True)

        cmd = "git commit -m'add file'" 
        subprocess.call(cmd, stdout=worker_log, stderr=worker_log, shell=True)

        thread_upload = Thread(target=runUpload, args=(new_file, upload_log))
        thread_upload.start()

def runUpload(new_file, log):
    cmd = "git push data master" 
    subprocess.call(cmd, stdout=log, stderr=log, shell=True)

    cmd = "rm " + new_file
    subprocess.call(cmd, stdout=log, stderr=log, shell=True)

def get_total_results(dir_path):
    cmd = "cat " + dir_path + "/OSquery-result.xml | grep 'subtitle'"
    out = subprocess.check_output(cmd, shell=True)
    p = re.compile("of (.*) total")
    max = p.search(out)
    return max.group(1)

def untracked_file_name(dir_path):
    cmd = "git status -s | grep '?? " + dir_path + "' | awk '{ print $2 }'"
    return subprocess.check_output(cmd, shell=True)

def read_file(file_r):
    file_r.seek(0)
    return file_r.read()

def overwrite_file(file_path, msg):
    file_o = open(file_path, 'w+')
    file_o.write(msg)

def main():
    lonlat = "-6.117176708154047,35.429154357361384:-5.998938062810441,35.579892441113685" #morocco, allysah
    
    #YYYY-MM-DDThh:mm:ss.cccZ
    start_2014 = "2014-01-01T00:00:00.000Z"
    end_2014 = "2014-12-31T23:59:59.000Z"

    start_2015 = "2015-01-01T00:00:00.000Z"
    end_2015 = "2015-12-31T23:59:59.000Z"

    start_2016 = "2016-01-01T00:00:00.000Z"
    end_2016 = "2016-12-31T23:59:59.000Z"

    start_2017 = "2017-01-01T00:00:00.000Z"
    end_2017 = "2017-12-31T23:59:59.000Z"

    # ommit './'
    dir_path_2014 = "morocco/2014"
    dir_path_2015 = "morocco/2015"
    dir_path_2016 = "morocco/2016"
    dir_path_2017 = "morocco/2017"

    cmd = "mkdir -p " + dir_path_2014
    subprocess.call(cmd, shell=True)

    cmd = "mkdir -p " + dir_path_2015
    subprocess.call(cmd, shell=True)

    cmd = "mkdir -p " + dir_path_2016
    subprocess.call(cmd, shell=True)

    cmd = "mkdir -p " + dir_path_2017
    subprocess.call(cmd, shell=True)
   
    query_log = open('query_log.txt', 'w+')

    progress_2014 = open(dir_path_2014 + '/progress.txt', 'a+')
    worker_log_2014 = open(dir_path_2014 + '/worker_log.txt', 'w+')
    upload_log_2014 = open(dir_path_2014 + '/upload_log.txt', 'w+')

    progress_2015 = open(dir_path_2015 + '/progress.txt', 'a+')
    worker_log_2015 = open(dir_path_2015 + '/worker_log.txt', 'w+')
    upload_log_2015 = open(dir_path_2015 + '/upload_log.txt', 'w+')

    progress_2016 = open(dir_path_2016 + '/progress.txt', 'a+')
    worker_log_2016 = open(dir_path_2016 + '/worker_log.txt', 'w+')
    upload_log_2016 = open(dir_path_2016 + '/upload_log.txt', 'w+')

    progress_2017 = open(dir_path_2017 + '/progress.txt', 'a+')
    worker_log_2017 = open(dir_path_2017 + '/worker_log.txt', 'w+')
    upload_log_2017 = open(dir_path_2017 + '/upload_log.txt', 'w+')

    cmd = "git add --all" 
    subprocess.call(cmd, shell=True)

    resume14 = read_file(progress_2014)
    resume15 = read_file(progress_2015)
    resume16 = read_file(progress_2016)
    resume17 = read_file(progress_2017)

    if resume14 == '':
        resume14 = 1

    if resume15 == '':
        resume15 = 1

    if resume16 == '':
        resume16 = 1

    if resume17 == '':
        resume17 = 1

    runQuery(secrets.worker1_username, secrets.worker1_password, lonlat, start_2014, end_2014, query_log)
    max2014 = get_total_results(".")
    print("total results in 2014: " + max2014)
    
    runQuery(secrets.worker2_username, secrets.worker2_password, lonlat, start_2015, end_2015, query_log)
    max2015 = get_total_results(".")
    print("total results in 2015: " + max2015) 

    runQuery(secrets.worker3_username, secrets.worker3_password, lonlat, start_2016, end_2016, query_log)
    max2016 = get_total_results(".")
    print("total results in 2016: " + max2016)
    
    runQuery(secrets.worker4_username, secrets.worker4_password, lonlat, start_2017, end_2017, query_log)
    max2017 = get_total_results(".")
    print("total results in 2017: " + max2017)
    
    #thread_2014 = Thread(target=runWorker, args=(secrets.worker1_username, secrets.worker1_password, lonlat, start_2014, end_2014, dir_path_2014, max2014, worker_log_2014)) 
    thread_2017 = Thread(target=runWorker, args=(secrets.worker4_username, secrets.worker4_password, lonlat, start_2017, end_2017, dir_path_2017, resume17, max2017, worker_log_2017, upload_log_2017)) 
    
    #thread_2014.start()
    thread_2017.start()

if __name__ == "__main__":
    main()