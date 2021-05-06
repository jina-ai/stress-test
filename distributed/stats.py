import os
import glob
import chevron
import requests
import pandas as pd
from itertools import product
from datetime import timedelta
from prettytable import PrettyTable

from logger import logger, LOGS_DIR

SLACK_MESSAGE_JSON = 'slack-message.json'
tasks = ['index', 'search']
types = ['numpy+binarypb', 'annoy+binarypb', 'faiss+binarypb']
clients = ['grpc', 'websocket']


def collect_and_push(slack=False):
    df_list = []

    table = PrettyTable()
    table.field_names = ["Task", "VecIndexer", "KVIndexer", "Client", "#Clients",
                         "Total Time (hrs)", "#Docs", "Docs per sec"]

    for stats_file in glob.glob(f'{LOGS_DIR}/p2p*.log'):
        df_list.append(pd.read_json(stats_file, lines=True))

    stats_df = pd.concat(df_list, axis=0, ignore_index=True)

    for _task, _type, _client in product(tasks, types, clients):
        temp_df = stats_df[(stats_df.task == _task) &
                        (stats_df.type == _type) &
                        (stats_df.client == _client)]

        logger.info(f'Configuration: task: {_task}, type: {_type}, client: {_client}, '
                    f'num_clients: {len(temp_df.process_id.unique())}')

        if len(temp_df) > 0:
            _num_clients = len(temp_df.process_id.unique())

            _total_client_roundtrip_time_secs = temp_df.client_roundtrip.sum() / 1000
            _total_client_roundtrip_time_hrs = str(timedelta(seconds=int(_total_client_roundtrip_time_secs)))
            _total_jina_docs = temp_df.num_jina_docs.sum()
            avg_jina_docs_per_sec = _total_jina_docs / _total_client_roundtrip_time_secs
            logger.info(f'Total Client Roundtrip Time: '
                        f'{_total_client_roundtrip_time_secs:.2f} secs / {_total_client_roundtrip_time_hrs} hours')
            logger.info(f'Total Number of Jina Documents: {_total_jina_docs}')
            logger.info(f'Avg Jina Documents per sec: {avg_jina_docs_per_sec:.2f}')

            _vec_indexer, _kv_indexer = map(str.title, _type.split('+'))
            table.add_row(
                [_task, _vec_indexer, _kv_indexer, _client, _num_clients,
                 _total_client_roundtrip_time_hrs, _total_jina_docs, f'{avg_jina_docs_per_sec:.1f}']
            )
        else:
            logger.warning(f'Current config not triggered')

    with open(f'{LOGS_DIR}/stats.txt', 'w') as f:
        f.write(str(table))

    if slack:
        push_to_slack(STRESS_TEST_RESULTS=str(table).replace('\n', '\\n'),
                      TFID=5678)

    return table


def push_to_slack(**kwargs):
    if 'STRESS_TEST_SLACK_WEBHOOK' not in os.environ:
        logger.error(f'Slack webhook env var is not set. Please set it to allow slack message push!')
        raise EnvironmentError(f'Please set Slack related env vars')

    with open(SLACK_MESSAGE_JSON) as f:
        message_payload = chevron.render(f, kwargs)
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url=os.getenv('STRESS_TEST_SLACK_WEBHOOK'),
                          data=message_payload,
                          headers=headers)
        if r.status_code != 200:
            r.raise_for_status()
