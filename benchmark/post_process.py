import pandas as pd


def clean_dataframe(filepath: str = 'routes.parquet'):
    """ Reads parquet file & creates a dataframe """
    routes_df = pd.read_parquet(filepath)
    for c in routes_df.columns:
        routes_df[[f'{c}_start_time', f'{c}_end_time']] = \
            pd.DataFrame(routes_df[c].tolist(), index= routes_df.index)
        routes_df.drop(columns=c, inplace=True)
    return routes_df


def evaluate_times(routes_df, num_docs, num_pods):
    """ Evaluates different timestamps from the dataframe """
    existing_cols = routes_df.columns
    for i in range(num_pods + 1):
        if i == 0:
            routes_df['g->p0:send'] = routes_df['pod0_start_time'] - routes_df['gateway_start_time'] 
        elif i == num_pods:
            ## This needs fix as routes_df['gateway_end_time'] & routes_df['pod1_end_time'] are None (hence defaulting)
            # routes_df[f'p{i-1}->g:send'] = routes_df['gateway_end_time'] - routes_df[f'pod{i-1}_start_time']
            continue
        else:
            routes_df[f'p{i-1}->p{i}:send'] = routes_df[f'pod{i}_start_time'] - routes_df[f'pod{i-1}_start_time'] 
    
    # Redundant
    # routes_df['g->p0:send'] = routes_df['pod0_start_time'] - routes_df['gateway_start_time'] 
    # routes_df['p0->p1:send'] = routes_df['pod1_start_time'] - routes_df['pod0_end_time'] 
    
    ## This needs fix as routes_df['gateway_end_time'] & routes_df['pod1_end_time'] are None (hence defaulting
    # routes_df['roundtrip'] = routes_df['gateway_end_time'] - routes_df['gateway_start_time'] 
    
    cnames_for_send = [f'pod{i}_start_time' for i in range(num_pods-1, -1, -1)] + ['gateway_start_time']
    for i in range(len(cnames_for_send)-1):
        current_send = routes_df[cnames_for_send[i]] - routes_df[cnames_for_send[i+1]]
        if i == 0:
            total_send = current_send
        else:
            total_send += current_send

    routes_df['g:send'] = total_send
    
    cnames_for_recv = [f'pod{i}_end_time' for i in range(num_pods-1, -1, -1)] + ['gateway_end_time']
    for i in range(len(cnames_for_recv)-1):
        current_recv = routes_df[cnames_for_recv[i]] - routes_df[cnames_for_recv[i+1]]
        if i == 0:
            total_recv = current_recv
        else:
            total_recv += current_recv
    
    ## This needs fix as routes_df['gateway_end_time'] & routes_df['pod1_end_time'] are None (hence defaulting)
    # routes_df['g:recv'] = total_recv
    
    ## This needs fix as routes_df['gateway_end_time'] & routes_df['pod1_end_time'] are None (hence defaulting)
    # routes_df['docs/s'] = num_docs / (routes_df['roundtrip'].seconds)

    columns_of_interest = list(set(routes_df.columns) - set(existing_cols))
    return routes_df, columns_of_interest


def get_summary(routes_df, columns_of_interest):
    """ Returns Stats summary of the timestamps """
    summary = {}
    for _ in columns_of_interest:
        summary[_] = {}
        summary[_]['mean'] = routes_df[_].mean().total_seconds()
        summary[_]['median'] = routes_df[_].median().total_seconds()
        summary[_]['std'] = routes_df[_].std().total_seconds()
        summary[_]['max'] = routes_df[_].max().total_seconds()
        summary[_]['min'] = routes_df[_].min().total_seconds()
        summary[_]['sum'] = routes_df[_].sum().total_seconds()
    return summary
