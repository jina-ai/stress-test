import click
import matplotlib.pyplot as plt
import json
import pandas as pd


@click.command()
@click.option('--recall_at', '-k', default=10)
def create_plot(recall_at):
    if recall_at is 1:
        k = 0
    elif recall_at is 10:
        k = 1
    elif recall_at is 20:
        k = 2
    elif recall_at is 50:
        k = 3
    elif recall_at is 100:
        k = 4
    else:
        print("K value not valid. It should be either 1, 10, 20, 50 or 100. K = 10 will be used")
        k = 1


    input_file = open('results.json')
    json_array = json.load(input_file)

    result_list = []
    recall_list = []

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
        recall_list.append(inner_l[k])

    plt.plot(recall_list, query_time*60)
    _recall_at = "recall@" + str(recall_at)
    plt.ylabel('query_time')
    plt.xlabel(_recall_at)

    plt.show()


if __name__ == "__main__":
    create_plot()
