import os

from jina.executors.indexers.vector.numpy import NumpyIndexer

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")


def get_numpy_indexer(params):
    name = params['name']
    return NumpyIndexer(index_filename=f'{name}.tgz', compress_level=1,
                        metas={'workspace': WORKSPACE_DIR,
                               'warn_unnamed': False,
                               'separated_workspace': False,
                               'is_trained': False,
                               'max_snapshot': 0
                               })
