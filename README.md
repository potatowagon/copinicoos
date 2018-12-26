# Copinicoos
Copernicus-downloader. Downloads all the results in a search query in seperate threads, and uploads to a remote git repository so Windows users may access it too. The data on local is deleted after it is uploaded to minimise disk usage. Made to run unattended on a server.

<img src="img/1.PNG" width="400">

### Installation
First install python. Then clone or download (.zip) this repository. Runs only on Unix systems, ie. Linux and Mac
```
git clone https://github.com/potatowagon/copinicoos.git
```

### Setup 
cd to cloned repository, and give run access to the setup script
```
chmod +x setup.sh
./setup.sh
```

#### Set Remote repository
The git repository where downloaded data will be uploaded to.
```
git remote add data <my remote repository>
```

#### Set Copernicus Open Hub accounts
This bot uses 4 Copernicus open hub accounts to download 4 items simultaneously. An empty `secrets.py` file has been created during the setup phase. Please fill in the following in secrets.py

```
worker1_username = "fill in username"
worker1_password = "fill in password"

worker2_username = "fill in username"
worker2_password = "fill in password"

worker3_username = "fill in username"
worker3_password = "fill in password"

worker4_username = "fill in username"
worker4_password = "fill in password"

```

### Run
Edit `main.py` to adjust search query. For examaple, `lonlat` sepcifies query location, `start_date` and `end_date` specifies query sensing time window.

To run
```
python main.py
```

### Troubleshoot

If you see the system spitting out concurrent downloading request without downloading that looks something like this

```
morocco/2017/dhusget.sh -u copinicoos2 -p sondra11 -T GRD -m "Sentinel-1" -c "-6.117176708154047,35.429154357361384:-5.998938062810441,35.579892441113685" -S 2017-01-01T00:00:00.000Z -E 2017-12-31T23:59:59.000Z -l 1 -P 1 -o product -O morocco/2017 -w 5 -W 30 -L morocco/2017/dhusget_lock -n 4 -q morocco/2017/OSquery-result.xml -C morocco/2017/products-list.csv
morocco/2017/dhusget.sh -u copinicoos2 -p sondra11 -T GRD -m "Sentinel-1" -c "-6.117176708154047,35.429154357361384:-5.998938062810441,35.579892441113685" -S 2017-01-01T00:00:00.000Z -E 2017-12-31T23:59:59.000Z -l 1 -P 2 -o product -O morocco/2017 -w 5 -W 30 -L morocco/2017/dhusget_lock -n 4 -q morocco/2017/OSquery-result.xml -C morocco/2017/products-list.csv
morocco/2017/dhusget.sh -u copinicoos2 -p sondra11 -T GRD -m "Sentinel-1" -c "-6.117176708154047,35.429154357361384:-5.998938062810441,35.579892441113685" -S 2017-01-01T00:00:00.000Z -E 2017-12-31T23:59:59.000Z -l 1 -P 3 -o product -O morocco/2017 -w 5 -W 30 -L morocco/2017/dhusget_lock -n 4 -q morocco/2017/OSquery-result.xml -C morocco/2017/products-list.csv
morocco/2017/dhusget.sh -u copinicoos2 -p sondra11 -T GRD -m "Sentinel-1" -c "-6.117176708154047,35.429154357361384:-5.998938062810441,35.579892441113685" -S 2017-01-01T00:00:00.000Z -E 2017-12-31T23:59:59.000Z -l 1 -P 4 -o product -O morocco/2017 -w 5 -W 30 -L morocco/2017/dhusget_lock -n 4 -q morocco/2017/OSquery-result.xml -C morocco/2017/products-list.csv
...
```
It is highly likely because the lock folder `dhusget_lock` was not deleted due to sudden termination of a previous run.

To resolve delete all `dhusget_lock` folders

```
find . -name dhusget_lock -type d -exec rm -r {} +
```

Error logs can be found in `worker_log.txt` and `upload_log.txt` in workdir of each Worker

``` 
cat ./path/to/workdir/worker_log.txt
```
