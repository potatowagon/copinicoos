def req_search_res_json(query):
        query = query.strip()
        if not query.startswith('https://scihub.copernicus.eu/dhus/search?q=') and not query.endswith('&format=json'):
            request_done_str = "Request Done: "
            if query.startswith(request_done_str):
                query = query.replace(request_done_str, "")
            
            if query.startswith('"') and query.endswith('"'):
                query = query[1:len(query)-1]

            if query.startswith("'") and query.endswith("'"):
                query = query[1:len(query)-1]

            query = 'https://scihub.copernicus.eu/dhus/search?q=' + query + '&format=json'
        return query

def adjust_for_specific_product(query):
    if not query.startswith('https://scihub.copernicus.eu/dhus/search?q=') and not query.endswith('&format=json'):
        query = req_search_res_json(query)
    return append_rows_start(query)
        

def append_rows_start(query):
    if not "&rows=1" in query:
            query = query[:len(query)] + "&rows=1" 
    if not "&start=" in query:
        query = query[:len(query)] + "&start=" 
    return query


