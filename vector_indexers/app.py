import click
import json
import numpy as np
import os


from jina.executors import BaseExecutor

from annoy_indexer import get_annoy_indexer
from faiss_indexer import get_faiss_indexer
from numpy_indexer import get_numpy_indexer
from load_experiment import load_experiment
from read_vectors_files import fvecs_read, ivecs_read
from perf_timer import PerfTimer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
FAISS_DATA_DIR = os.path.join(os.path.join(os.path.dirname(__file__), "faiss_data"), "sift")
INDEX_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_base.fvecs")
QUERY_FEED_PATH = os.path.join(FAISS_DATA_DIR, "sift_query.fvecs")
GROUNDTRUTH_PATH = os.path.join(FAISS_DATA_DIR, 'sift_groundtruth.ivecs')

INDEX_TYPE = 'index_type'
PARAMS = 'params'
INDEX_TIME_S = 'index_time'
INDEX_DOCS = 'index_docs'
INDEX_DOCS_S = 'index_docs_s'
BUILD_TIME_S = 'build_time'
QUERY_TIME = 'query_time'
QUERY_DOCS = 'query_docs'
QUERY_DOCS_S = 'query_docs_s'
RECALL = 'recall@1,10,20,50,100'


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


def do_index(indexer: 'BaseNumpyIndexer', batch_size: int, stat: dict):
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(INDEX_FEED_PATH, batch_size):
            indexer.add(keys, vecs)
            n += batch_size
    stat[INDEX_TIME_S] = t.interval
    stat[INDEX_DOCS] = n
    stat[INDEX_DOCS_S] = n / t.interval
    print(f'Took {t.interval} seconds to index {n} documents: {n / t.interval} doc/s')


def do_warmup(indexer: 'BaseNumpyIndexer', stat: dict):
    t = PerfTimer()
    with t:
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size=1, max_docs=100):
            indexer.query(vecs, 1)
    stat[BUILD_TIME_S] = t.interval
    print(f'Took {t.interval} seconds to train and warmup the index')


def do_query(indexer: 'BaseNumpyIndexer', batch_size: int, top_k: int, stat: dict):
    results = np.empty((0, top_k), 'float32')
    t = PerfTimer()
    with t:
        n = 0
        for keys, vecs in read_data(QUERY_FEED_PATH, batch_size):
            doc_ids, dists = indexer.query(vecs, top_k)
            if doc_ids.shape != (keys.shape[0],):
                results = np.vstack((results, doc_ids))
            n += batch_size
    stat[QUERY_TIME] = t.interval
    stat[QUERY_DOCS] = n
    stat[QUERY_DOCS_S] = n / t.interval
    print(f'Took {t.interval} seconds to query {n} documents: {n / t.interval} doc/s')
    return results


def do_evaluate(results: np.array, stat: dict):
    groundtruth = ivecs_read(GROUNDTRUTH_PATH)
    if results.shape[0] < groundtruth.shape[0]:
        add_negative = np.full((groundtruth.shape[0] - results.shape[0], results.shape[1]), -1)
        results = np.vstack((results, add_negative))

    def recall_at_k(k):
        """
        Computes how many times the true nearest neighbour is returned as one of the k closest vectors from a query.
        Taken from https://gist.github.com/mdouze/046c1960bc82801e6b40ed8ee677d33e
        """
        eval = (results[:, :k] == groundtruth[:, :1]).sum() / float(results.shape[0])
        return eval

    for eval_point in [1, 10, 20, 50, 100]:
        result_evaluation = recall_at_k(eval_point)
        stat[RECALL].append(result_evaluation)
        print(f'recall@{eval_point} = {result_evaluation}')


def get_indexer(index_type, params):
    if index_type == 'faiss':
        return get_faiss_indexer(params)
    elif index_type == 'annoy':
        return get_annoy_indexer(params)
    elif index_type == 'numpy':
        return get_numpy_indexer(params)


def load_indexer(abs_path):
    return BaseExecutor.load(abs_path)


@click.command()
@click.option('--batch_size', '-n', default=50)
@click.option('--top_k', '-k', default=100)
@click.option('--file_path', '-f', type=str, default='experiments.yaml')
@click.option('--index', '-i', is_flag=True)
@click.option('--warmup', '-w', is_flag=True)
@click.option('--query', '-q', is_flag=True)
@click.option('--evaluate', '-e', is_flag=True)
def run(batch_size, top_k, file_path, index, warmup, query, evaluate):
    print(f'Testing from file {file_path}')
    for index_type, params in load_experiment(file_path):
        stat = {
            INDEX_TYPE: index_type,
            PARAMS: params,
            INDEX_TIME_S: 0,
            INDEX_DOCS: 0,
            INDEX_DOCS_S: 0,
            BUILD_TIME_S: 0,
            QUERY_TIME: 0,
            QUERY_DOCS: 0,
            QUERY_DOCS_S: 0,
            RECALL: []
        }
        print(f'Testing for index {index_type} with params {params}')
        params_str = str(params).encode('utf-8').hex()
        index_str = f'{index_type}-{params_str}'
        save_path = os.path.join(WORKSPACE_DIR, f"{index_str}.bin")
        params['name'] = index_str
        with get_indexer(index_type, params) as idx:
            if index:
                do_index(idx, batch_size, stat)
                idx.save(save_path)

        with load_indexer(save_path) as idx:
            if warmup:
                do_warmup(idx, stat)
            if query:
                results = do_query(idx, batch_size, top_k, stat)
                if evaluate:
                    do_evaluate(results, stat)
        with open('results.json', 'a') as f:
            json.dump(stat, f)


if __name__ == '__main__':
    run()
