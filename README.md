[![Build Status](https://travis-ci.org/potatowagon/copinicoos.svg?branch=master)](https://travis-ci.org/potatowagon/copinicoos)
[![codecov](https://codecov.io/gh/potatowagon/copinicoos/branch/master/graph/badge.svg)](https://codecov.io/gh/potatowagon/copinicoos)
![python version](https://img.shields.io/badge/python-3.6%20%7C%203.7-blue.svg)
[![Platform support](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey.svg)](https://travis-ci.org/potatowagon/copinicoos)
[![GitHub license](https://img.shields.io/github/license/potatowagon/copinicoos)](https://github.com/potatowagon/copinicoos/blob/master/LICENSE) 
[![Join the chat at https://gitter.im/copinicoos/community](https://badges.gitter.im/copinicoos/community.svg)](https://gitter.im/copinicoos/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Copinicoos
Copinicoos is a <a href="https://scihub.copernicus.eu/dhus/#/home">Copernicus</a> download manager. 

Copinicoos can ...
1. Automate the download of all results in a search query. 
2. Download in parallel processes, for faster downloads. 
3. Manage polling for offline products. 
4. Stop and resume downloads, anytime!

- [Copinicoos](#copinicoos)
  - [Install](#install)
  - [Usage](#usage)
    - [Interactive Mode](#interactive-mode)
      - [Resume download](#resume-download)
    - [Argparse Mode](#argparse-mode)
      - [resume](#resume)
      - [fresh](#fresh)
      - [For more details:](#for-more-details)
  - [Logs](#logs)
  - [Development](#development)
    - [Architecture](#architecture)
      - [Initialise and Setup](#initialise-and-setup)
    - [Testing](#testing)

## Install

```
pip install copinicoos
```

## Usage
### Interactive Mode

![](img/i_mode.gif)

To launch,
```
py -m copinicoos
```
And then follow on-screen prompt:

1. Enter Download Directory. Where products will be downloaded to. Entering nothing will default to current directory.
   
2. Enter number of Corpernicus accounts. Each account will initialise 2 parallel download processes.
   
3. Authenticate accounts by entering login credentials.
   
4. Enter query. This can be obtained from Copernicus Open Hub `Request Done: ( ... )`. Just copy that whole string.

5. Enter Polling Interval. Entering nothing will use default.

6. Enter offline product download retries. Entering nothing will use default.

#### Resume download
![](img/i_mode_resume.gif)

Again, launch 
```
py -m copinicoos
```
And then follow on-screen prompt:

1. Enter download directory containing `copinicoos_logs`. Or, if current working directory has `copinicoos_logs`, entering nothing will resume download from current working directory's savepoint. Savepoints are stored inside `copinicoos_logs`.

2. Agree to resume download 

3. Enter Polling Interval. Entering nothing will use default.

4. Enter offline product download retries. Entering nothing will use default.

### Argparse Mode

This mode is so that copinicoos can be called from a script.

All options:
```
py -m copinicoos <subcommand> -d <download-location> -r <offline-retries> -p <polling-interval>
```
Subcommand:
- resume 

- fresh

#### resume

```
py -m copinicoos resume
```
Resume download from savepoint in current working directory.

```
py -m copinicoos resume -d <download directory>
```
Resume download from savepoint in `<download directory>`.

#### fresh
```
py -m copinicoos fresh <query> <credentials>
```
Start a fresh download. 

Input can be read from a text file by affixing `@` to file name eg.

```
py -m copinicoos fresh @query.txt @secrets.json
```

eg. Inside `query.txt`
```
( footprint:"Intersects(POLYGON((91.45532862800384 22.42016942838278,91.34620270146559 22.43895934481047,91.32598614177974 22.336847270362682,91.4350291249018 22.31804599405974,91.45532862800384 22.42016942838278)))" ) AND ( (platformname:Sentinel-1 AND producttype:GRD))
```

eg. Inside `secrets.json`
```
{
    "u1":"username1",
    "p1":"password1",
    "u2":"username2",
    "p2":"password2"
}
```

Note: `"` has to be escaped, ie `\"`, if parsing directly to the cmd.

#### For more details:
```
py -m copinicoos --help
```

## Logs
Logs can be found in a folder named `copinicoos_logs` in the same directory where products are downloaded to. Manually deleting `copinicoos_logs` will restart the download.

A summary of finished downloads can be found in `copinicoos_logs\WorkerManager.log`. Resume points are saved in `<InstanceName>_progress.txt`

## Development

Source code is in `copinicoos\copinicoos`

cd to where setup.py is and
```
pip install -e .[dev]
```
This installs the dependencies needed for the development environment found under setup.py extras, and runs copinicoos from the dev enviroment, which is to run the code in this repo. All changes are automatically reflected in the dev enviroment. 

### Architecture

#### Initialise and Setup
![](img/init.png)

### Testing

Tests reside in the tests/ folder. Uses pytest framework.

Some unit tests need credentials to run. Due to security reasons, the account credentials used for testing are not commited to git. First, create test data with credentials.

`tests/test_data/secrets1.json`
```
{"u1":"username1","p1":"password1"}
```

`tests/test_data/secrets2.json`
```
{
    "u1":"username1",
    "p1":"password1",
    "u2":"username2",
    "p2":"password2"
}
```

To run all unit test cases
```
pytest -m "not e2e"
```

To run end to end test
```
pytest -m "e2e"
```
