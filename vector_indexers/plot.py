import matplotlib.pyplot as plt
import json
import pandas as pd



def create_plot():
    pointsList = []
    with open('test.json') as f:
        for jsonObj in f:
            pointDict = json.loads(jsonObj)
            pointsList.append(pointDict)

    df = pd.DataFrame(pointsList)
    dfg = df.groupby('query_time').count()

    plt.scatter(x=dfg.index, y=dfg['recall@1,10,20,50,100'])

    plt.show()

    dfg.plot()


if __name__ == "__main__":
    create_plot()
