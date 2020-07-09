import click
import os
import numpy as np
from jina.executors import BaseExecutor
from jina.executors.indexers.vector.faiss import FaissIndexer
from jina.executors.indexers.vector.annoy import AnnoyIndexer
from jina.executors.indexers.vector.numpy import NumpyIndexer
from read_vectors_files import fvecs_read, ivecs_read
from perf_timer import PerfTimer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
FAISS_DATA_DIR = os.path.join(os.path.join(os.path.dirname(__file__), "faiss_data"), "sift")
INDEX_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_base.fvecs")
QUERY_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_query.fvecs")
GROUNDTRUTH_PATH = os.path.join(FAISS_DATA_DIR, 'sift_groundtruth.ivecs')
FAISS_INDEXER_BIN_SAVE_PATH = os.path.join(WORKSPACE_DIR, "faiss-indexer.bin")
ANNOY_INDEXER_BIN_SAVE_PATH = os.path.join(WORKSPACE_DIR, "annoy-indexer.bin")
NUMPY_INDEXER_BIN_SAVE_PATH = os.path.join(WORKSPACE_DIR, "numpy-indexer.bin")


def read_data(db_file_path: str, batch_size: int, max_docs: int = None):
    vectors = fvecs_read(db_file_path)
    num_vectors = vectors.shape[0]
    batch_size = 1 if batch_size == -1 else batch_size
    num_batches = int(num_vectors / batch_size)

    if max_docs is not None:
        batch_size = max_docs
        num_batches = 1

    for i in range(1, num_batches + 1):
        start_batch = (i - 1) * batch_size
        end_batch = i * batch_size if i * batch_size < num_vectors else num_vectors
        keys = np.arange(start_batch, end_batch).reshape(end_batch - start_batch, 1)
        yield keys, vectors[start_batch: end_batch]


def do_index(indexer: 'BaseNumpyIndexer', batch_size: int):
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(INDEX_FEED_PATH, batch_size):
            indexer.add(keys, vecs)
            n += batch_size
    print(f'Took {t.interval} seconds to index {n} documents: {n / t.interval} doc/s')


def do_warmup(indexer: 'BaseNumpyIndexer'):
    t = PerfTimer()
    with t:
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size=1, max_docs=100):
            indexer.query(vecs, 1)
    print(f'Took {t.interval} seconds to train and warmup the index')


def do_query(indexer: 'BaseNumpyIndexer', batch_size: int, top_k: int):
    results = np.empty((0, top_k), 'float32')
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size):
            doc_ids, dists = indexer.query(vecs, top_k)
            results = np.vstack((results, doc_ids))
            n += batch_size
    print(f'Took {t.interval} seconds to query {n} documents: {n / t.interval} doc/s')
    return results


def do_evaluate(results: np.array):
    groundtruth = ivecs_read(GROUNDTRUTH_PATH)

    def recall_at_k(k):
        """
        Computes how many times the true nearest neighbour is returned as one of the k closest vectors from a query.
        Taken from https://gist.github.com/mdouze/046c1960bc82801e6b40ed8ee677d33e
        """
        eval = (results[:, :k] == groundtruth[:, :1]).sum() / float(results.shape[0])
        return eval

    for eval_point in [1, 10, 20, 50, 100]:
        print(f'recall@{eval_point} = {recall_at_k(eval_point)}')


def get_faiss_indexer(save_abspath: str = None):
    if save_abspath is None or os.path.exists(save_abspath) is False:
        return FaissIndexer(index_key='IVF4096,PQ64', train_filepath=os.path.join(WORKSPACE_DIR, "train.tgz"),
                            index_filename="faiss-index.tgz", compress_level=1,
                            metas={'workspace': WORKSPACE_DIR,
                                   'warn_unnamed': False,
                                   'separated_workspace': False,
                                   'is_trained': False,
                                   'max_snapshot': 0,
                                   'on_gpu': False
                                   })
    else:
        return BaseExecutor.load(save_abspath)


def get_annoy_indexer(save_abspath: str = None):
    if save_abspath is None or os.path.exists(save_abspath) is False:
        return AnnoyIndexer(metric='euclidean', ntrees=10,
                            index_filename="annoy-index.tgz", compress_level=1,
                            metas={'workspace': WORKSPACE_DIR,
                                   'warn_unnamed': False,
                                   'separated_workspace': False,
                                   'is_trained': False,
                                   'max_snapshot': 0
                                   })
    else:
        return BaseExecutor.load(save_abspath)


def get_numpy_indexer(save_abspath: str = None):
    if save_abspath is None or os.path.exists(save_abspath) is False:
        return NumpyIndexer(index_filename="numpy-index.tgz", compress_level=1,
                            metas={'workspace': WORKSPACE_DIR,
                                   'warn_unnamed': False,
                                   'separated_workspace': False,
                                   'is_trained': False,
                                   'max_snapshot': 0
                                   })
    else:
        return BaseExecutor.load(save_abspath)


def get_indexer(index_type: str = 'faiss'):
    if index_type == 'faiss':
        return get_faiss_indexer(FAISS_INDEXER_BIN_SAVE_PATH)
    elif index_type == 'annoy':
        return get_annoy_indexer(ANNOY_INDEXER_BIN_SAVE_PATH)
    elif index_type == 'numpy':
        return get_numpy_indexer(NUMPY_INDEXER_BIN_SAVE_PATH)


def save_indexer(indexer: 'BaseNumpyIndexer', index_type: str = 'faiss'):
    if index_type == 'faiss':
        indexer.save(FAISS_INDEXER_BIN_SAVE_PATH)
    elif index_type == 'annoy':
        indexer.save(ANNOY_INDEXER_BIN_SAVE_PATH)
    elif index_type == 'numpy':
        indexer.save(NUMPY_INDEXER_BIN_SAVE_PATH)


@click.command()
@click.option('--batch_size', '-n', default=50)
@click.option('--top_k', '-k', default=100)
@click.option('--index_type', '-t', default='faiss')
@click.option('--index', '-i', default=False, type=bool)
@click.option('--warmup', '-w', default=False, type=bool)
@click.option('--query', '-q', default=False, type=bool)
@click.option('--evaluate', '-e', default=False, type=bool)
def main(batch_size, top_k, index_type, index, warmup, query, evaluate):
    print(f'Testing for index {index_type}')
    with get_indexer(index_type) as idx:
        if index:
            do_index(idx, batch_size)
            save_indexer(idx, index_type)

    with get_indexer(index_type) as idx:
        if warmup:
            do_warmup(idx)
        if query:
            results = do_query(idx, batch_size, top_k)
            if evaluate:
                do_evaluate(results)


if __name__ == '__main__':
    main()
