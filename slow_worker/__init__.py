import numpy as np
from jina.drivers.helper import array2blob
from jina.proto import jina_pb2


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.embedding.CopyFrom(array2blob(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d
