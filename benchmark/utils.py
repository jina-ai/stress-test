import os
from typing import Iterator, List

import numpy as np
from google.protobuf.json_format import MessageToDict

from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


def configure_env():
    # convert to int while using env variables
    os.environ['START_NUM_DOCS'] = os.environ.get('START_NUM_DOCS', str(2 ** 15))
    os.environ['MULTIPLIER_NUM_DOCS'] = os.environ.get('MULTIPLIER_NUM_DOCS', '2')
    os.environ['COUNT_NUM_DOCS'] = os.environ.get('COUNT_NUM_DOCS', '5')
    os.environ['BATCH_SIZE'] = os.environ.get('BATCH_SIZE', '256')
    os.environ['EMBED_DIM'] = os.environ.get('EMBED_DIM', '16')
    os.environ['FILE_DIR'] = os.environ.get('FILE_DIR', '.data')
    os.makedirs(os.environ['FILE_DIR'], exist_ok=True)
    
    
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


