import os
import random

import pytest

from conftest import test_data_dir

@pytest.mark.parametrize(
    "result_num", [
        (1),
        (60),
        (150)
    ]
)
def test_query_product_uri_success(worker, result_num):
    title, product_uri = worker.query_product_uri(result_num)
    try:
        assert title.startswith("S1A") == True
        assert product_uri.startswith('"https://scihub.copernicus.eu/dhus/odata/v1/Products(') == True
        assert product_uri.endswith('/$value"') == True
    except Exception as e:
        print(title, product_uri)
        raise

def test_download_began(worker):
    assert worker.download_began(os.path.join(test_data_dir, "S1A_offline.zip")) == False
    assert worker.download_began(os.path.join(test_data_dir, "S1A_online.zip")) == True

@pytest.mark.parametrize(
    "result_num", [
        (random.randint(150,200))
    ]
)
def test_run_offline(worker, result_num):
    worker.run(result_num)