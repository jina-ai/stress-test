import os
import json
import time
import random
from enum import Enum
from shutil import copyfile
from typing import Dict, List
from datetime import datetime

import chevron
import numpy as np
from jina import Document, Request
from pydantic import FilePath, validate_arguments

from logger import logger

RENDER_DIR = '_rendered'
IMG_HEIGHT = 224
IMG_WIDTH = 224

_random_names = ('first', 'great', 'local', 'small', 'right', 'large', 'young', 'early', 'major', 'clear', 'black',
                 'whole', 'third', 'white', 'short', 'human', 'royal', 'wrong', 'legal', 'final', 'close', 'total',
                 'prime', 'happy', 'sorry', 'basic', 'aware', 'ready', 'green', 'heavy', 'extra', 'civil', 'chief',
                 'usual', 'front', 'fresh', 'joint', 'alone', 'rural', 'light', 'equal', 'quiet', 'quick', 'daily',
                 'urban', 'upper', 'moral', 'vital', 'empty', 'brief', 'world', 'house', 'place', 'group', 'party',
                 'money', 'point', 'state', 'night', 'water', 'thing', 'order', 'power', 'court', 'level', 'child',
                 'south', 'staff', 'woman', 'north', 'sense', 'death', 'range', 'table', 'trade', 'study', 'other',
                 'price', 'class', 'union', 'value', 'paper', 'right', 'voice', 'stage', 'light', 'march', 'board',
                 'month', 'music', 'field', 'award', 'issue', 'basis', 'front', 'heart', 'force', 'model', 'space',
                 'peter')


class GatewayClients(Enum):
    GRPC = 'grpc'
    WEBSOCKET = 'websocket'


def random_sentences(length) -> str:
    return ' '.join(random.choice(_random_names) for _ in range(length))


def create_random_img_array(img_height, img_width):
    return np.random.randint(0, 256, (img_height, img_width, 3))


def random_images(num_docs: int = 100):
    for idx in range(num_docs):
        with Document() as doc:
            doc.content = create_random_img_array(IMG_HEIGHT, IMG_WIDTH)
            doc.mime_type = 'image/png'
            doc.tags['filename'] = f'image {idx}'
            doc.tags['timestamp'] = str(time.time())
        yield doc


def random_texts(num_docs: int = 100):
    for idx in range(num_docs):
        with Document() as doc:
            doc.text = random_sentences(random.randint(1, 20))
            doc.tags['filename'] = f'filename {idx}'
            doc.tags['timestamp'] = str(time.time())
            num_chunks = random.randint(1, 10)
            for _ in range(num_chunks):
                doc.text += '. ' + random_sentences(random.randint(1, 20))
        yield doc


def _log_time_per_pod(routes: List,
                      timestamp: float,
                      state: Dict = {},
                      task: str = 'search',
                      **kwargs):
    from logger import p2p_metrics_logger
    state[f'{task}_doc_counter'] = 1 if f'{task}_doc_counter' not in state else state[f'{task}_doc_counter'] + 1

    def _time_diff_ms(start, end):
        _time_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
        return (datetime.strptime(end, _time_fmt) - datetime.strptime(start, _time_fmt)).total_seconds() * 1000

    time_per_pod = {i['pod']: f'{_time_diff_ms(i["startTime"], i["endTime"]):.0f}' for i in routes}
    p2p_metrics_logger.info(json.dumps(
        {'task': task,
         'doc_count': state[f'{task}_doc_counter'],
         **kwargs,
         'client_roundtrip': f'{(time.time() - timestamp) * 1000:.0f}',
         **time_per_pod}
    ))


def validate_images(resp: Request, top_k: int = 10, **kwargs):
    from steps import StepItems
    task = 'index' if 'index' in resp.dict().keys() else 'search'
    timestamp_from_tags = float(resp.dict()[task]['docs'][0]['tags']['timestamp'])
    _log_time_per_pod(routes=resp.dict()['routes'][:-1],
                      timestamp=timestamp_from_tags,
                      state=StepItems.state,
                      task=task, **kwargs)

    for d in resp.search.docs:
        if len(d.matches) != top_k:
            logger.error(f'Number of actual matches: {len(d.matches)} vs expected number: {top_k}')
        for m in d.matches:
            if 'timestamp' not in m.tags.keys():
                logger.error(f'timestampe not in tags: {m.tags}')
            if 'filename' not in m.tags.keys():
                logger.error(f'filename not in tags: {m.tags}')
            # to test that the data from the KV store is retrieved
            if 'image ' not in m.tags['filename']:
                logger.error(f'"image" not in m.tags["filename"]: {m.tags["filename"]}')


def validate_texts(resp: Request, top_k: int = 10, **kwargs):
    from steps import StepItems
    task = 'index' if 'index' in resp.dict().keys() else 'search'
    timestamp_from_tags = float(resp.dict()[task]['docs'][0]['tags']['timestamp'])
    _log_time_per_pod(routes=resp.dict()['routes'][:-1],
                      timestamp=timestamp_from_tags,
                      state=StepItems.state,
                      task=task, **kwargs)

    for d in resp.search.docs:
        if len(d.matches) != top_k:
            logger.error(f'Number of actual matches: {len(d.matches)} vs expected number: {top_k}')
        for m in d.matches:
            # to test that the data from the KV store is retrieved
            if 'filename' not in m.tags.keys():
                logger.error(f'did not find "filename" in tags: {m.tags}')


@validate_arguments
def set_environment_vars(files: List[FilePath], environment: Dict[str, str]):
    os.makedirs(RENDER_DIR, exist_ok=True)
    for file in files:
        copyfile(file, f'{RENDER_DIR}/{file.name}')
        with open(file, 'r') as org_file, open(f'{RENDER_DIR}/{file.name}', 'w') as rendered_file:
            content_to_be_rendered = chevron.render(org_file, environment)
            rendered_file.write(content_to_be_rendered)
