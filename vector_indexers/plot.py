import matplotlib.pyplot as plt
import json
import pandas as pd


def create_plot():

    input_file = open('results.json')
    json_array = json.load(input_file)
    result_list = []

    for item in json_array:
        result_details = {"query_time": None, "recall@1,10,20,50,100": None}
        result_details['query_time'] = item['query_time']
        result_details['recall@1,10,20,50,100'] = item['recall@1,10,20,50,100']
        result_list.append(result_details)

    result_list_dataframe = pd.DataFrame(result_list)
    dfg = result_list_dataframe.groupby('query_time').count()

    plt.scatter(x=dfg.index, y=dfg['recall@1,10,20,50,100'])
    plt.ylabel('recall@1,10,20,50,100 ')
    plt.xlabel('query_time ')

    plt.show()

    dfg.plot()


if __name__ == "__main__":
    create_plot()
