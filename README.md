[![Build Status](https://travis-ci.org/potatowagon/copinicoos.svg?branch=remove-dhusget)](https://travis-ci.org/potatowagon/copinicoos)

# Copinicoos
<a href="https://scihub.copernicus.eu/dhus/#/home">Copernicus</a>-downloader. Downloads the results in a search query in parallel processes, for faster downloads

## Install

After downloading repo, cd to root of this repo (where setup.py is) and pip install
```
pip install .
```

## Usage
### Interactive Mode
![](img/i_mode.gif)

To launch,
```
py -m copinicoos
```
And then follow on-screen prompt:

1. Enter number of workers
   
2. Activate workers by entering copernicus hub account credentials. The account is used by worker to download products.
   
3. Enter query. This can be obtained from Copernicus Open Hub `Request Done: ( ... )`. Just copy that whole string.
   
4. Enter Download Directory. Where products will be downloaded to. Entering nothing will default to current directory.

5. Enter Polling Interval. Entering nothing will use default.

6. Enter offline product download retries. Entering nothing will use default.

### Argparse Mode

## Development

### Architecture

### Testing
To run all unit test cases
```
pytest -m "not e2e"
```

To run end to end test
```
pytest -m "e2e"
```