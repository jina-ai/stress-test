import datetime
import os
import uuid
import glob
import chevron
import requests
import pandas as pd
from itertools import product
from datetime import timedelta
from prettytable import PrettyTable

import warnings
warnings.filterwarnings('ignore')

from logger import logger, LOGS_DIR
SLACK_MESSAGE_JSON = 'configs/slack-message.json'
# TODO: This is error prone. Maybe we should read it from config yaml
tasks = ['index', 'search']
types = ['Numpy+BinaryPb+ImageTorch', 'Annoy+BinaryPb+ImageTorch', 'Faiss+BinaryPb+ImageTorch',
         'Numpy+Redis+ImageTorch', 'Annoy+Redis+ImageTorch', 'Faiss+Redis+ImageTorch',
         'NumpyIndexer+BinaryPb+TransformerTorch', 'Annoy+BinaryPb+TransformerTorch']
clients = ['grpc', 'websocket']


def collect_and_push(slack=False):
    df_list = []

    table = PrettyTable()
    table.add_column(
        'Experiments',
        ['Task', 'VecIndexer', 'KVIndexer', 'Encoder', 'Client', '#Clients',
         'Total Time (C2C, wall clock time)', 'Total Time (processing time)', '#Docs', '# Docs per sec (C2C)', '# Docs per sec (G2G)',
         'Time spent (VecIndexer)', 'Time spent (KVIndexer)', 'Time spent (Encoder)',
         'Time spent (Segmenter)', 'Time spent (join_all)', 'Time spent (ranker)']
    )

    for stats_file in glob.glob(f'{LOGS_DIR}/p2p*.log'):
        df_list.append(pd.read_json(stats_file, lines=True))

    stats_df = pd.concat(df_list, axis=0, ignore_index=True)

    experiment_idx = 0
    for _task, _type, _client in product(tasks, types, clients):
        temp_df = stats_df[(stats_df.task == _task) & (stats_df.type == _type) & (stats_df.client == _client)]

        _num_clients = len(temp_df.process_id.unique())


        _pods = set()
        _total_time_spent_dict = {}

        if _num_clients > 0:
            logger.info(f'Configuration: task: {_task}, type: {_type}, client: {_client}, num_clients: {_num_clients}')
            for _pod_shard in temp_df.columns[temp_df.columns.str.contains('ZEDRuntime')].str.replace('/ZEDRuntime', '').str.split('/'):
                # TODO: we can get total time at each shard
                try:
                    _pod, _shard = _pod_shard
                except ValueError:
                    _pod = _pod_shard[0]
                    _shard = None
                _pods.add(_pod)

            def total_time_spent_str(column):
                return str(timedelta(seconds=int(temp_df[column].sum() / 1000 / _num_clients)))

            def total_time_spent_str_pods(column):
                return str(timedelta(seconds=int(temp_df[column].sum() / 1000)))

            for _pod in _pods:
                cols = temp_df.columns[(temp_df.columns.str.contains(_pod))]
                temp_df[cols].fillna(0, inplace=True)
                temp_df[cols] = temp_df[cols].clip(lower=0)
                temp_df[f'{_pod}_time_spent_per_doc_per_client'] = temp_df[cols].sum(axis=1)
                _total_time_spent_dict[_pod] = total_time_spent_str_pods(f'{_pod}_time_spent_per_doc_per_client')

            _total_time_spent_dict['client'] = total_time_spent_str('client_roundtrip')
            _total_jina_docs = temp_df.num_jina_docs.sum()
            _avg_jina_docs_per_sec_c2c = _num_clients * _total_jina_docs / (temp_df['client_roundtrip'].sum() / 1000)
            _avg_jina_docs_per_sec_g2g = _num_clients * _total_jina_docs / (temp_df['gateway'].sum() / 1000)

            logger.info(f'Total Client Roundtrip Time: {_total_time_spent_dict["client"]} hours')
            logger.info(f'Total Number of Jina Documents: {_total_jina_docs}')
            logger.info(f'Avg Jina Documents per sec: {_avg_jina_docs_per_sec_c2c:.2f}')

            try:
                _vec_indexer, _kv_indexer, _encoder = _type.split('+')
            except ValueError:
                _vec_indexer, _kv_indexer, _encoder = ['unknown'] * 3

            experiment_idx += 1

            def seconds(x): return (datetime.datetime.strptime(x[1], "%H:%M:%S") - datetime.datetime(1900, 1, 1)).total_seconds()

            total_time_spent = sum(map(seconds, filter(lambda item: True if item[0] != 'client' else False, _total_time_spent_dict.items())))
            total_time_spent_str = str(timedelta(seconds=total_time_spent))

            # TODO: Below names are hardcoded (not picked from actual pods). Flow yaml with different name would break this.
            table.add_column(
                f'Experiment {experiment_idx}',
                [_task, _vec_indexer, _kv_indexer, _encoder, _client, _num_clients,
                 _total_time_spent_dict['client'],  total_time_spent_str, _total_jina_docs,
                 f'{_avg_jina_docs_per_sec_c2c:.1f}', f'{_avg_jina_docs_per_sec_g2g:.1f}',
                 _total_time_spent_dict['vec_idx'],  _total_time_spent_dict['doc_idx'],
                 _total_time_spent_dict['encoder'],
                 _total_time_spent_dict['segmenter'] if 'segmenter' in _total_time_spent_dict else 'n/a',
                 _total_time_spent_dict['join_all'] if 'join_all' in _total_time_spent_dict else 'n/a',
                 _total_time_spent_dict['ranker'] if 'ranker' in _total_time_spent_dict else 'n/a']
            )

    with open(f'{LOGS_DIR}/stats.txt', 'w') as f:
        f.write(str(table))

    if slack:
        push_to_slack(STRESS_TEST_RESULTS=str(table).replace('\n', '\\n'),
                      TFID=os.getenv('TFID') if 'TFID' in os.environ else str(uuid.uuid4()))

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
