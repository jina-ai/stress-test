import os
import uuid
from math import ceil

import click
from jina.flow import Flow

from post_process import clean_dataframe, evaluate_times, get_summary
from utils import random_docs_generator, random_bytes_generator, generate_filename, get_list_of_num_docs
from summary import html_table, plot_num_docs_vs_time


def configure_env():
    # convert to int while using env variables
    os.environ['START_NUM_DOCS'] = os.environ.get('START_NUM_DOCS', '512')
    os.environ['MULTIPLIER_NUM_DOCS'] = os.environ.get('MULTIPLIER_NUM_DOCS', '4')
    os.environ['COUNT_NUM_DOCS'] = os.environ.get('COUNT_NUM_DOCS', '10')
    os.environ['BATCH_SIZE'] = os.environ.get('BATCH_SIZE', '256')
    os.environ['EMBED_DIM'] = os.environ.get('EMBED_DIM', '16')
    os.environ['FILE_DIR'] = os.environ.get('FILE_DIR', './.data')
    os.makedirs(os.environ['FILE_DIR'], exist_ok=True)
    
    
COLUMN_OF_INTEREST = 'g:send' # to be changed to 'roundtrip' once issue is fixed


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
    with f:
        f.search(input_fn=input_fn)


@click.command()
@click.option('--index-type', '-i', type=click.Choice(['bytes', 'jina_pb2.Document', 'sentences']), default='bytes')
@click.option('--index-yaml', default='index.yml')
@click.option('--query-yaml', default='query.yml')
@click.option('--num-bytes-per-doc', default=10)
@click.option('--num-chunks-per-doc', default=5)
@click.option('--num-sentences-per-doc', default=10)
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
        file_name = generate_filename(num_docs, index_type)
        file_path = os.path.join(os.path.dirname(__file__), f"{os.environ['FILE_DIR']}/{file_name}")
        os.environ['FILE_PATH'] = file_path
        
        pod_names = index(yaml_path=index_yaml,
                          num_docs=num_docs,
                          index_type=index_type,
                          num_bytes_per_doc=num_bytes_per_doc,
                          num_chunks_per_doc=num_chunks_per_doc,
                          num_sentences_per_doc=num_sentences_per_doc)
        query(yaml_path=query_yaml,
              num_docs=1)
        
        routes_df = clean_dataframe(file_path=file_path)
        routes_df, columns_of_interest = evaluate_times(routes_df=routes_df, 
                                                        num_docs=num_docs, 
                                                        pod_names=pod_names)
        current_summary = get_summary(routes_df=routes_df,
                                      columns_of_interest=columns_of_interest)
        overall_summary[num_docs] = current_summary
    #     os.remove(f'{FILE_DIR}/{filename}')

    print(overall_summary)
    html_table_text = html_table(overall_summary_dict=overall_summary)
    uuid_gen = uuid.uuid4().hex.lower()[0:10]
    image_filename = plot_num_docs_vs_time(overall_summary_dict=overall_summary,
                                           column_of_interest=COLUMN_OF_INTEREST,
                                           uid=uuid_gen) # to be changed to gh hash
    with open('README.MD', 'w') as readme_f:
        readme_f.write('<h3>Results</h3>')
        readme_f.write(html_table_text)
        readme_f.write('\n\n\n<h3>Num docs vs Time<h3>\n\n')
        readme_f.write(f'![Num docs vs Time]({image_filename})')


if __name__ == '__main__':
    run_benchmark()
