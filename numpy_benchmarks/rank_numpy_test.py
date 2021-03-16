# This pull request https://github.com/jina-ai/jina/pull/2163  provided an alternative
# group by with less array creation. This file benchmarks the change with respect to the
# previous code implementation

import numpy as np

COL_STR_TYPE = 'U64'  
        
def get_data_batch(n, 
                   n_cols = 4,
                   n_parent_ids = 10,
                   n_max=100,
                   type_cols = [COL_STR_TYPE, COL_STR_TYPE, COL_STR_TYPE, np.float ]):

    match_idx = np.zeros((n,n_cols))
    
    doc_id = np.random.randint(0,n_parent_ids,n)
    chunk_id1 = np.random.randint(0,n_max,n)
    chunk_id2 = np.random.randint(0,n_max,n)
    scores = np.random.rand(n)
    
    r = [(a1,a2,a2,a4) for a1,a2,a2,a4 in zip(doc_id,chunk_id1, chunk_id2, scores)]
    return np.array(r,  dtype=[
                ('c0', COL_STR_TYPE),
                ('c1', COL_STR_TYPE),
                ('c2', COL_STR_TYPE),
                ('c3', np.float)])

######### Current Jina code

def _sort_doc_by_score(r):
    r = np.array(
        r,
        dtype=[
            ('ids', COL_STR_TYPE),
            ('scores', np.float64),
        ],
    )
    return np.sort(r, order='scores')[::-1]

def _score_list(_groups):    
    r = []
    for _g in _groups:
        match_id = _g[0]['c0']
        score = np.random.rand()
        r.append((match_id, score))

    return _sort_doc_by_score(r)

def _group_by(match_idx, col_name):
    _sorted_m = np.sort(match_idx, order=col_name)
    _, _doc_counts = np.unique(_sorted_m[col_name], return_counts=True)
    return np.split(_sorted_m, np.cumsum(_doc_counts))[:-1]


######### Proposed Jina code

def _score_list_optimized(_groups):
    n_groups = len(_groups)
    res = np.empty((n_groups,), dtype=[('ids','U64'), ('scores', np.float64)] )
    for i,_g in enumerate(_groups):
        res[i] = (_g['c0'][0], np.random.rand())
    return res

def _score_optimized(_groups):
    res = _score_list_optimized(_groups)
    res[::-1].sort(order='scores')
    return res

def _group_by_optimized(match_idx, col_name):
    _sorted_m = np.sort(match_idx, order=col_name)
    n_elements = len(_sorted_m[col_name])
    list_numpy_arrays = []
    prev_val = _sorted_m[col_name][0]
    prev_index = 0
    for i, current_val in enumerate(_sorted_m[col_name]):
        if current_val != prev_val:
            list_numpy_arrays.append(_sorted_m[prev_index:i])
            prev_index = i
            prev_val = current_val
    if current_val == prev_val:
        list_numpy_arrays.append(_sorted_m[prev_index:])

    return list_numpy_arrays

if __name__ == '__main__':

    import timeit    
    import pandas as pd
    
    n_repetitions = 100000
    n_retrieved_items_tests = [10,20,30,40,50,60,70,80,90,100,500]

    times_original = []
    times_optimized = []

    print('\nCurrent Jina _group_by')
    for n_retrieved_items in n_retrieved_items_tests:    
        t_original = timeit.timeit('_group_by(match_idx,"c0")',number=n_repetitions,
                      setup=f"""from __main__ import _group_by, get_data_batch;\\
                                n_retrieved_items={n_retrieved_items};\\
                                match_idx = get_data_batch(n_retrieved_items)""")
        t_original = round(t_original,2)

        print(f'\tn_repetitions={n_repetitions}, n_retrieved_items={n_retrieved_items}, time={t_original} sec')
        times_original.append(t_original)

    print('\nOptimized proposal _group_by_optimized')
    for n_retrieved_items in n_retrieved_items_tests:    
        t_optimized = timeit.timeit('_group_by_optimized(match_idx,"c0")',number=n_repetitions,
                      setup=f"""from __main__ import _group_by_optimized, get_data_batch;\\
                                n_retrieved_items={n_retrieved_items};\\
                                match_idx = get_data_batch(n_retrieved_items)""")
        t_optimized = round(t_optimized,2)
        print(f'\tn_repetitions={n_repetitions}, n_retrieved_items={n_retrieved_items}, time={t_optimized} sec')
        times_optimized.append(t_optimized)

    ## Gather results and plot a table
    result = pd.DataFrame({'original execution times (sec)':times_original, 
                           'optimized execution times (sec)':times_optimized},
                           index = n_retrieved_items_tests)
    result.index.name = 'n_retrieved_items'
    print(f'\nTable results')
    print(result)
