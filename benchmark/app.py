import os
import sys
from math import ceil

import yaml
import click
from jina.flow import Flow

from post_process import clean_dataframe, evaluate_times, \
    get_summary, write_benchmark_to_markdown
from utils import is_config_set, configure_file_path, random_docs_generator, \
    random_bytes_generator, get_list_of_num_docs


def index(yaml_path, num_docs, input_type='bytes', batch_size=256, embed_dim=16,
          num_bytes_per_doc=10, num_chunks_per_doc=5, num_sentences_per_doc=5):
    if input_type == 'bytes':
        input_fn = random_bytes_generator(num_docs=num_docs, 
                                          num_bytes=num_bytes_per_doc)
    elif input_type == 'jina_pb2.Document':
        input_fn = random_docs_generator(num_docs=num_docs, 
                                         chunks_per_doc=num_chunks_per_doc, 
                                         embed_dim=embed_dim)
    elif input_type == 'sentences':
        pass
        
    f = Flow().load_config(filename=yaml_path)
    f = f.add(name='benchmark_pod', 
              uses=f'yamls/pods/benchmark_driver.yml')
    with f:
        f.index(input_fn=input_fn, 
                batch_size=batch_size)
        
    return list(f._pod_nodes.keys())


def query(yaml_path, num_docs=1, index_type='bytes', embed_dim=16):
    if index_type == 'bytes':
        input_fn = random_bytes_generator(num_docs=1, 
                                          num_bytes=10)
    elif index_type == 'jina_pb2.Document':
        input_fn = random_docs_generator(num_docs=1, 
                                         chunks_per_doc=5, 
                                         embed_dim=embed_dim)
    elif index_type == 'sentences':
        pass
    f = Flow().load_config(filename=yaml_path)
    f = f.add(name='benchmark_pod',
              uses='yamls/pods/benchmark_driver.yml')
    with f:
        f.search(input_fn=input_fn)
    
    return list(f._pod_nodes.keys())


def run_benchmark():
    env = is_config_set()
    if not env:
        print(f'Exiting..')
        sys.exit(-1)
    index_yaml = os.path.join(os.path.dirname(__file__), env['INDEX_YAML'])
    query_yaml = os.path.join(os.path.dirname(__file__), env['QUERY_YAML'])
    print(index_yaml)
    overall_summary = {
        'index': {},
        'query': {}
    }

    for num_docs in env['NUM_DOCS']:
        os.environ['NUM_EPOCHS'] = str(ceil(num_docs / env['BATCH_SIZE']))
        index_file_path = configure_file_path(num_docs=num_docs, 
                                              op_type='index', 
                                              input_type=env['INPUT_TYPE'],
                                              file_dir=env['FILE_DIR'])     
        index_pod_names = index(yaml_path=index_yaml,
                                num_docs=num_docs,
                                input_type=env['INPUT_TYPE'],
                                batch_size=env['BATCH_SIZE'],
                                embed_dim=env['EMBED_DIM'],
                                num_bytes_per_doc=env['NUM_BYTES_PER_DOC'],
                                num_chunks_per_doc=env['NUM_CHUNKS_PER_DOC'],
                                num_sentences_per_doc=env['NUM_SENTENCES_PER_DOC'])
        
        query_file_path = configure_file_path(num_docs=num_docs, 
                                              op_type='query', 
                                              input_type=env['INPUT_TYPE'],
                                              file_dir=env['FILE_DIR'])
        query_pod_names = query(yaml_path=query_yaml,
                                num_docs=1,
                                embed_dim=env['EMBED_DIM'])
        
        index_routes_df = clean_dataframe(file_path=index_file_path)
        index_routes_df, columns_of_interest = evaluate_times(routes_df=index_routes_df, 
                                                        num_docs=num_docs, 
                                                        pod_names=index_pod_names)
        current_index_summary = get_summary(routes_df=index_routes_df,
                                            columns_of_interest=columns_of_interest)
        overall_summary['index'][num_docs] = current_index_summary
        
        # query_routes_df = clean_dataframe(file_path=query_file_path)
        # query_routes_df, columns_of_interest = evaluate_times(routes_df=query_routes_df, 
        #                                                       num_docs=1, 
        #                                                       pod_names=query_pod_names)
        # current_query_summary = get_summary(routes_df=query_routes_df,
        #                                     columns_of_interest=columns_of_interest)
        
        # overall_summary['query'][num_docs] = current_query_summary
    
    
    with open('overall_summary.yml', 'w') as summary_f:
        yaml.dump(overall_summary, summary_f, default_flow_style=False)


if __name__ == '__main__':
    run_benchmark()
