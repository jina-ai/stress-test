import click
import matplotlib.pyplot as plt
import json
import pandas as pd


@click.command()
@click.option('--recall_at', '-k', default=0)
def create_plot(recall_at):
    input_file = open('results.json')
    json_array = json.load(input_file)

    result_list = []
    result_y = []

    for item in json_array:
        result_details = {"index_time": None,
                          "index_docs": None,
                          "query_time": None,
                          "build_time": None,
                          "query_docs": None,
                          "recall@1,10,20,50,100": None}

        result_details['index_docs'] = item['index_docs']
        result_details['index_docs'] = item['index_docs']
        result_details['query_time'] = item['query_time']
        result_details['build_time'] = item['build_time']
        result_details['query_docs'] = item['query_docs']
        result_details['recall@1,10,20,50,100'] = item['recall@1,10,20,50,100']
        result_list.append(result_details)

    result_list_dataframe = pd.DataFrame(result_list)
    query_time = result_list_dataframe['query_time']

    recall_at_k = result_list_dataframe['recall@1,10,20,50,100']

    for inner_l in recall_at_k:
        result_y.append(inner_l[recall_at])

    plt.plot(query_time, result_y)
    _recall_at = "recall@" + str(recall_at)
    plt.ylabel(_recall_at)
    plt.xlabel('query_time ')

    plt.show()


if __name__ == "__main__":
    create_plot()
