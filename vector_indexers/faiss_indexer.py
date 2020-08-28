import os

from jina.hub.indexers.vector.FaissIndexer import FaissIndexer
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")


def get_faiss_indexer(params):
    n_list = params['n_list']
    n_probe = params['n_probes']
    name = params['name']
    return FaissIndexer(index_key=f'IVF{n_list},Flat', n_probe=n_probe,
                        train_filepath=os.path.join(WORKSPACE_DIR, f'{name}.tgz'),
                        index_filename=f'{name}.tgz', compress_level=1,
                        metas={'workspace': WORKSPACE_DIR,
                               'warn_unnamed': False,
                               'separated_workspace': False,
                               'is_trained': False,
                               'max_snapshot': 0,
                               'on_gpu': False
                               })
