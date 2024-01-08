import json
from commons.utils import get_model_id, get_opensearch_client

CLIENT = get_opensearch_client()

def execute_query(query, pipeline_id=None, index='abstracts', source_includes=['_id', 'fragment_id'], source_excludes=[], size=5):
    '''
    Execute a query on the OpenSearch index.
    :param query: The query to execute.
    :param pipeline_id: The id of the pipeline to execute the query on. If None, no pipeline is used. 
    !IMPORTANT: The pipeline must be registered on the cluster. If you use a hybrid query, the pipeline_id should be specified.
    :param index: The index to execute the query on.
    :param source_includes: The fields to include in the response.
    :param source_excludes: The fields to exclude in the response.
    :param size: The number of results to return.
    :return: The response from OpenSearch.
    '''

    query_body = {
        'size': size,
        'query': query
    }

    match pipeline_id:
        case None:
            return CLIENT.search(
                body=query_body,
                index=index,
                _source_includes=source_includes,
                _source_excludes=source_excludes,
            )
        case _:
            return CLIENT.search(
                body=query_body,
                index=index,
                _source_includes=source_includes,
                _source_excludes=source_excludes,
                params={
                    'search_pipeline': pipeline_id
                }
    )

def extract_hits_from_response(response):
    '''
    Post-process the response from OpenSearch.
    If no hits are found, an empty list is returned.
    :param response: The response from OpenSearch.
    :return: The post-processed response.
    '''
    try:
        hits = response['hits']['hits']
    except KeyError:
        print('No hits found.')
        return []
    
    return hits

def create_simple_match_query(query_text, match_on='abstract_fragment'):
    return {
        'match': {
            match_on: {
                'query': query_text
            }
        }
    }

def create_multimatch_query(query_text, match_on_fields=['abstract_fragment', 'title', 'keyword_list']):
    return {
        'multi_match': {
            'query': query_text,
            'fields': match_on_fields
        }
    }


def create_neural_query(query_text):
    return {
        'neural': {
            'abstract_fragment_embedding': {
                'query_text': query_text,
                'model_id': get_model_id(CLIENT)
            }
        }
    }

def create_hybrid_multimatch_neural_query(query_text, match_on_fields=['abstract_fragment', 'title', 'keyword_list']):
    return {
        'hybrid': {
            'queries': [
                create_multimatch_query(query_text, match_on_fields),
                create_neural_query(query_text)
            ],
        }
    }


if __name__ == "__main__":
    query_simple_match = create_simple_match_query('artificial intelligence')

    query_hybrid_multimatch_neural = create_hybrid_multimatch_neural_query(
        query_text = 'artificial intelligence',
        match_on_fields = ['abstract_fragment', 'title', 'keyword_list']
        )
    
    response = execute_query(
        query = query_hybrid_multimatch_neural, 
        pipeline_id = 'basic-nlp-search-pipeline',
        index = 'abstracts',
        size=2,
        source_includes=['_id', 'fragment_id', 'title']
        )
    hits = extract_hits_from_response(response)
    print(json.dumps(hits, indent=2))


