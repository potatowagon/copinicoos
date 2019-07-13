import pytest

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