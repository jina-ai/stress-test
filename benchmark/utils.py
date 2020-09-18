import os
from typing import Iterator, List

import yaml
import numpy as np
from google.protobuf.json_format import MessageToDict

from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


def load_config():
    try:
        with open('config.yml') as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        print(e)
        

def is_config_set():
    config = load_config()
    env = config['env']
    allowed_input_types = ['bytes', 'ndarray', 'jina_pb2.Document']
    try:
        if env['INPUT_TYPE'] not in allowed_input_types:
            print(f'Invalid input type {env["INPUT_TYPE"]}. Allowed {allowed_input_types}')
            return False
        if not os.path.isfile(env['INDEX_YAML']):
            print(f'Index file doesn\'t exist')
            return False
        if not os.path.isfile(env['QUERY_YAML']):
            print(f'Query file doesn\'t exist')
            return False
        if not isinstance(env['NUM_DOCS'], list):
            print(f'Invalid NUM_DOCS')
            return False
        if not isinstance(env['BATCH_SIZE'], int) or\
            not isinstance(env['EMBED_DIM'], int):
            print("Invalid batch size or embed size")
            return False 
        os.makedirs(env['FILE_DIR'], exist_ok=True)
        return True
    except KeyError as exp:
        print(f'Following key doesn\'t exist {exp}')
    except Exception as exp:
        print(f'Got the following exception while checking configs {exp}')
        return False
    
    
def configure_file_path(num_docs, op_type, input_type):
    file_name = generate_filename(num_docs=num_docs, 
                                  op_type=op_type, 
                                  input_type=input_type)
    file_path = os.path.join(os.path.dirname(__file__), f"{os.environ['FILE_DIR']}/{file_name}")
    os.environ['FILE_PATH'] = file_path
    return file_path


def generate_filename(num_docs, op_type, input_type) -> str:
    """ Generates filename using num_docs, op_type, input_type """
    return f'docs_{num_docs}_{op_type}_{input_type}.parquet'


def random_bytes_generator(num_docs, num_bytes) -> Iterator[bytes]:
    """
    yields `num_bytes` bytes `num_docs` times
    """
    for _ in range(num_docs):
        yield b'a' * num_bytes


def random_docs_generator(num_docs, chunks_per_doc=5, embed_dim=10) -> Iterator[jina_pb2.Document]:
    """
    yields `jina_pb2.Document()` with `chunks_per_doc` chunks in each `num_docs` times 
    """
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.meta_info = b'hello world'
        d.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.id = c_id
            c.parent_id = j
            c_id += 1
        yield d


def random_sentences_generator(num_docs, lines_per_doc=5) -> Iterator[str]:
    pass


def get_list_of_num_docs(start, multiplier, count) -> List[int]:
    """
    returns list of `number of docs` to be indexed
    e.g. - for start=512, multiplier=4, count=4, returns [512, 2048, 8192, 32768]
    we'll run the stress-test for different num_docs & benchmark it 
    """
    return [int(start) * (int(multiplier) ** i) for i in range(int(count))]


