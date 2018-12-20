# Copinicoos
Copernicus-downloader. Downloads in seperate threads, and uploads to a remote git repository so Windows users may access it too.

### Installation
First install python. Then clone this repository. Runs only on Unix systems, ie. Linux and Mac

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
Edit `main.py` to adjust search query. For examaple, lonlat sepcifies query location, start_date and end_date specifies query sensing time window.

To run
```
python main.py
```
