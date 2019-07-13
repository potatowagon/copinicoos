import pytest

@pytest.mark.parametrize(
    "result_num", [
        (1),
        (60),
        (150)
    ]
)
def test_query_product_uri_success(worker, result_num):
    worker.query_product_uri(result_num)
