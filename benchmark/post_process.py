import os
import uuid
from typing import Dict

import pandas as pd
import matplotlib.pyplot as plt


COLUMN_OF_INTEREST = 'g:send' # to be changed to 'roundtrip' once issue is fixed

def clean_dataframe(file_path: str = 'routes.parquet') -> pd.DataFrame:
    routes_df = pd.read_parquet(file_path)
    # Dropping the last batch as end_time is defaulting
    routes_df.drop(routes_df.index[-1], inplace=True)
    
    columns_to_be_combined = {}
    for c in routes_df.columns:
        if c.endswith('-head') or c.endswith('-tail'):
            new_c_name = c.replace('-head', '').replace('-tail', '')
            c_combined = [_ for _ in routes_df.columns 
                          if new_c_name in _ and not _.endswith('-head') and not _.endswith('-tail')]

            try:    
                columns_to_be_combined[new_c_name].extend(c_combined)
            except KeyError:
                columns_to_be_combined[new_c_name] = []

    for k, v in columns_to_be_combined.items():
        routes_df[k] = routes_df[v[0]]
        del routes_df[v[0]]
        for i in range(1, len(v)):
            routes_df[k] = routes_df[k].fillna(routes_df[v[i]])
            del routes_df[v[i]]
    
    for c in routes_df.columns:
        routes_df[[f'{c}_start_time', f'{c}_end_time']] = \
            pd.DataFrame(routes_df[c].tolist(), index= routes_df.index)
        routes_df.drop(columns=c, inplace=True)
    return routes_df


def evaluate_times(routes_df, num_docs, pod_names):
    """ Evaluates different timestamps from the dataframe """
    if 'gateway' in pod_names: pod_names.remove('gateway')
    existing_cols = routes_df.columns
    
    for i in range(len(pod_names) + 1):
        if i == 0:
            # print(f'gateway->{pod_names[i]}:send = {pod_names[i]}_start_time - gateway_start_time')
            routes_df[f'gateway->{pod_names[i]}:send'] = routes_df[f'{pod_names[i]}_start_time'] - routes_df['gateway_start_time'] 
        elif i == len(pod_names):
            ## This needs fix as routes_df['gateway_end_time'] are None (hence defaulting)
            # print(f'{pod_names[i-1]}->gateway:send = gateway_end_time - {pod_names[i-1]}_start_time')
            # routes_df[f'{pod_names[i-1]}->gateway:send'] = routes_df['gateway_end_time'] - routes_df[f'{pod_names[i-1]}_start_time']
            continue
        else:
            # print(f'{pod_names[i-1]}->{pod_names[i]}:send = {pod_names[i]}_start_time - {pod_names[i-1]}_start_time')
            routes_df[f'{pod_names[i-1]}->{pod_names[i]}:send'] = routes_df[f'{pod_names[i]}_start_time'] - \
                                                routes_df[f'{pod_names[i-1]}_start_time']
    
    ## This needs fix as routes_df['gateway_end_time'] & routes_df['pod1_end_time'] are None (hence defaulting)
    # routes_df['roundtrip'] = routes_df['gateway_end_time'] - routes_df['gateway_start_time'] 
    
    columns_for_send = [c + '_start_time' for c in reversed(pod_names)] + ['gateway_start_time']
    for i in range(len(columns_for_send)-1):
        current_send = routes_df[columns_for_send[i]] - routes_df[columns_for_send[i+1]]
        if i == 0:
            total_send = current_send
        else:
            total_send += current_send

    routes_df['g:send'] = total_send
    
    columns_for_recv = [c + '_end_time' for c in reversed(pod_names)] # + ['gateway_end_time']
    for i in range(len(columns_for_recv)-1):
        current_recv = routes_df[columns_for_recv[i]] - routes_df[columns_for_recv[i+1]]
        if i == 0:
            total_recv = current_recv
        else:
            total_recv += current_recv

    ## This needs fix as routes_df['gateway_end_time'] is None (hence defaulting)
    routes_df['g:recv'] = total_recv
    
    ## This needs fix as routes_df['gateway_end_time'] is None (hence defaulting)
    # routes_df['docs/s'] = num_docs / (routes_df['roundtrip'].seconds)
    
    columns_of_interest = list(set(routes_df.columns) - set(existing_cols))
    return routes_df, columns_of_interest


def get_summary(routes_df, columns_of_interest) -> Dict:
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

def write_benchmark_to_markdown(overall_summary, click_help_msg):
    with open('README.template.MD') as template_md:
        template_text = template_md.readlines()
    
    print(overall_summary)
    html_table_text = html_table(overall_summary_dict=overall_summary)
    uuid_gen = uuid.uuid4().hex.lower()[0:10]
    image_filename = plot_num_docs_vs_time(overall_summary_dict=overall_summary,
                                           column_of_interest=COLUMN_OF_INTEREST,
                                           uid=uuid_gen,
                                           file_dir=os.environ['FILE_DIR']) # to be changed to gh hash
    with open('README.MD', 'w') as readme_f:
        readme_f.writelines(template_text)
        readme_f.write('<h3> Usage </h3>\n\n')
        readme_f.write(f'```\n{click_help_msg}\n```')
        readme_f.write('\n\n<h3>Results</h3>\n')
        readme_f.writelines(f'\n\n{html_table_text}')
        readme_f.write('\n\n\n<h3>Num docs vs Time<h3>\n\n')
        readme_f.write(f'![Num docs vs Time]({image_filename})')
    

def html_table(overall_summary_dict) -> str:
    table_html = ''
    for num_docs, summary in overall_summary_dict.items():
         table_html += pd.DataFrame(summary).loc['mean'].to_frame().rename(columns={'mean': num_docs}).T.round(3).to_html()
    return table_html


def plot_num_docs_vs_time(overall_summary_dict, column_of_interest, uid, file_dir) -> str:
    """ Plots num_docs (log scale) vs total time"""
    x, y = [], []
    for num_docs, summary in overall_summary_dict.items():
        x.append(num_docs)
        y.append(summary[column_of_interest]['sum'])
    plt.figure(figsize=(16, 4))
    plt.plot(x, y, linestyle='--', marker='o')
    plt.xlabel('Number of docs indexed')
    plt.ylabel(f'{column_of_interest} total time (secs)')
    plt.xscale('log', base=2)
    plt.tight_layout()
    image_filename = f'{file_dir}/num-docs-vs-time-{uid}.svg'
    plt.savefig(image_filename)
    return image_filename
