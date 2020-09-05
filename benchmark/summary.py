import os
from pandas import DataFrame
import matplotlib.pyplot as plt


FILE_DIR = os.environ.get('FILE_DIR', './.data')
os.makedirs(FILE_DIR, exist_ok=True)


def html_table(overall_summary_dict) -> str:
    table_html = ''
    for num_docs, summary in overall_summary_dict.items():
         table_html += DataFrame(summary).loc['mean'].to_frame().rename(columns={'mean': num_docs}).T.round(3).to_html()
    return table_html


def plot_num_docs_vs_time(overall_summary_dict, column_of_interest, uid) -> str:
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
    image_filename = f'{FILE_DIR}/num-docs-vs-time-{uid}.svg'
    plt.savefig(image_filename)
    return image_filename

