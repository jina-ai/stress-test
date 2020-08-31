import os



WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")


def get_annoy_indexer(params):
    from jina.hub.indexers.vector.AnnoyIndexer import AnnoyIndexer
    n_trees = params['n_trees']
    search_k = params['search_k']
    name = params['name']
    return AnnoyIndexer(metric='euclidean', ntrees=n_trees, search_k=search_k,
                        index_filename=f'{name}.tgz', compress_level=1,
                        metas={'workspace': WORKSPACE_DIR,
                               'warn_unnamed': False,
                               'separated_workspace': False,
                               'is_trained': False,
                               'max_snapshot': 0
                               })
