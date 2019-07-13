import pytest

from copinicoos import query_formatter

def test_req_search_res_json(query, formatted_query):
    fq = query_formatter.req_search_res_json(query)
    assert fq == formatted_query

def test_adjust_for_specific_product(query, formatted_query1):
    fq = query_formatter.adjust_for_specific_product(query)
    assert fq == formatted_query1

