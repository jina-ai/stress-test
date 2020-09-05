import os
from math import ceil

import click
from jina.flow import Flow

from post_process import clean_dataframe, evaluate_times, \
    get_summary, write_benchmark_to_markdown
from utils import configure_env, configure_file_path, random_docs_generator, \
    random_bytes_generator, get_list_of_num_docs


def index(yaml_path, num_docs, index_type='bytes', num_bytes_per_doc=10, num_chunks_per_doc=5, num_sentences_per_doc=5):
    if index_type == 'bytes':
        input_fn = random_bytes_generator(num_docs=num_docs, 
                                          num_bytes=num_bytes_per_doc)
    elif index_type == 'jina_pb2.Document':
        input_fn = random_docs_generator(num_docs=num_docs, 
                                         chunks_per_doc=num_chunks_per_doc, 
                                         embed_dim=int(os.environ['EMBED_DIM']))
    elif index_type == 'sentences':
        pass
        
    f = Flow().load_config(filename=yaml_path)
    f = f.add(name='benchmark_pod', 
              uses=f'yamls/pods/benchmark_driver.yml')
    with f:
        f.index(input_fn=input_fn, 
                batch_size=int(os.environ['BATCH_SIZE']))
        
    return list(f._pod_nodes.keys())


def query(yaml_path, num_docs=1, index_type='bytes', ):
    if index_type == 'bytes':
        input_fn = random_bytes_generator(num_docs=1, 
                                          num_bytes=10)
    elif index_type == 'jina_pb2.Document':
        input_fn = random_docs_generator(num_docs=1, 
                                         chunks_per_doc=5, 
                                         embed_dim=int(os.environ['EMBED_DIM']))
    elif index_type == 'sentences':
        pass
    f = Flow().load_config(filename=yaml_path)
    f = f.add(name='benchmark_pod',
              uses='yamls/pods/benchmark_driver.yml')
    with f:
        f.search(input_fn=input_fn)


@click.command()
@click.option('--index-type', 
              type=click.Choice(['bytes', 'jina_pb2.Document', 'sentences']), 
              default='bytes', 
              help='Type of input to be indexed & queried (Default - bytes)')
@click.option('--index-yaml', 
              default='index.yml',
              help='index yaml file to be loaded in the yamls directory (Default - index.yml)')
@click.option('--query-yaml', 
              default='query.yml',
              help='query yaml file to be loaded in the yamls directory (Default - query.yml)')
@click.option('--num-bytes-per-doc', 
              default=10,
              help='Default - 10')
@click.option('--num-chunks-per-doc', 
              default=5,
              help='Default - 5')
@click.option('--num-sentences-per-doc', 
              default=10,
              help='Default - 10')
def run_benchmark(index_type, index_yaml, query_yaml, num_bytes_per_doc, 
                  num_chunks_per_doc, num_sentences_per_doc):
    configure_env()
    index_yaml = os.path.join(os.path.dirname(__file__), f'yamls/{index_yaml}')
    query_yaml = os.path.join(os.path.dirname(__file__), f'yamls/{query_yaml}')
    overall_summary = {}
    for num_docs in get_list_of_num_docs(start=os.environ['START_NUM_DOCS'],
                                         multiplier=os.environ['MULTIPLIER_NUM_DOCS'],
                                         count=os.environ['COUNT_NUM_DOCS']):
        os.environ['NUM_EPOCHS'] = str(ceil(num_docs / int(os.environ['BATCH_SIZE'])))
        index_file_path = configure_file_path(num_docs=num_docs, 
                                              op_type='index', 
                                              input_type=index_type)     
        index_pod_names = index(yaml_path=index_yaml,
                                num_docs=num_docs,
                                index_type=index_type,
                                num_bytes_per_doc=num_bytes_per_doc,
                                num_chunks_per_doc=num_chunks_per_doc,
                                num_sentences_per_doc=num_sentences_per_doc)
        
        query_file_path = configure_file_path(num_docs=num_docs, 
                                              op_type='query', 
                                              input_type=index_type)
        query(yaml_path=query_yaml,
              num_docs=1)
        
        routes_df = clean_dataframe(file_path=index_file_path)
        routes_df, columns_of_interest = evaluate_times(routes_df=routes_df, 
                                                        num_docs=num_docs, 
                                                        pod_names=index_pod_names)
        current_index_summary = get_summary(routes_df=routes_df,
                                            columns_of_interest=columns_of_interest)
        overall_summary[num_docs] = current_index_summary
    #     os.remove(f'{FILE_DIR}/{filename}')
    ctx = click.get_current_context()
    click_help_msg = ctx.get_help()
    write_benchmark_to_markdown(overall_summary=overall_summary,
                                click_help_msg=click_help_msg)


if __name__ == '__main__':
    run_benchmark()
