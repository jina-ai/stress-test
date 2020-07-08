import click
import os
import numpy as np
from jina.executors import BaseExecutor
from jina.executors.indexers.vector.faiss import FaissIndexer
from jina.executors.indexers.vector import BaseNumpyIndexer
from read_vectors_files import fvecs_read, ivecs_read
from perf_timer import PerfTimer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
FAISS_DATA_DIR = os.path.join(os.path.join(os.path.dirname(__file__), "faiss_data"), "sift")
INDEX_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_base.fvecs")
QUERY_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_query.fvecs")
GROUNDTRUTH_PATH = os.path.join(FAISS_DATA_DIR, 'sift_groundtruth.ivecs')
INDEXER_BIN_SAVE_PATH = os.path.join(WORKSPACE_DIR, "indexer.bin")


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


def index(indexer: 'BaseNumpyIndexer', batch_size: int):
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(INDEX_FEED_PATH, batch_size):
            indexer.add(keys, vecs)
            n += batch_size
    print(f'Took {t.interval} m to index {n} documents: {n/t.interval}doc/s')


def train(indexer: 'BaseNumpyIndexer'):
    t = PerfTimer()
    with t:
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size=1, max_docs=100):
            indexer.query(vecs, 1)
    print(f'Took {t.interval} m to train and warmup the index')


def query(indexer: 'BaseNumpyIndexer', batch_size: int, top_k: int):
    results = np.empty((0, top_k), 'float32')
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size):
            doc_ids, dists = indexer.query(vecs, top_k)
            results = np.vstack((results, doc_ids))
            n += batch_size
    print(f'Took {t.interval} m to query {n} documents: {n/t.interval}doc/s')
    return results


def evaluate(results: np.array):
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


def get_indexer(save_abspath: str = None):
    if save_abspath is None:
        return FaissIndexer(index_key='IVF10,PQ4', train_filepath=os.path.join(WORKSPACE_DIR, "train.tgz"),
                            index_filename="index.tgz", compress_level=1,
                            metas={'workspace': WORKSPACE_DIR,
                                   'warn_unnamed': False,
                                   'separated_workspace': False,
                                   'is_trained': False,
                                   'max_snapshot': 0
                                   })
    else:
        return BaseExecutor.load(save_abspath)


@click.command()
@click.option('--batch_size', '-n', default=50)
@click.option('--top_k', '-k', default=100)
@click.option('--i', '-i', default=False, type=bool)
@click.option('--t', '-t', default=False, type=bool)
@click.option('--q', '-q', default=False, type=bool)
@click.option('--e', '-e', default=False, type=bool)
def main(batch_size, top_k, i, t, q, e):
    with get_indexer() as idx:
        if i:
            index(idx, batch_size)
            idx.save(INDEXER_BIN_SAVE_PATH)

    with get_indexer(save_abspath=INDEXER_BIN_SAVE_PATH) as idx:
        if t:
            train(idx)
        if q:
            results = query(idx, batch_size, top_k)
            if e:
                evaluate(results)


if __name__ == '__main__':
    main()
