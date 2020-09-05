from typing import Iterator, List
import numpy as np
from google.protobuf.json_format import MessageToDict

from jina.proto import jina_pb2
from jina.drivers.helper import array2pb


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


def generate_filename(num_docs, index_type) -> str:
    """ Generates filename using num_docs & index_type """
    return f'docs_{num_docs}_index_{index_type}.parquet'
