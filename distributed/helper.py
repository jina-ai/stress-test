import os
import random
from enum import Enum
from typing import Dict, List
from datetime import datetime
from shutil import copyfile

import chevron
import numpy as np
from jina import Document
from pydantic import FilePath
from pydantic.decorator import validate_arguments

from logger import logger, metric_logger

__all__ = [
    'random_images',
    'random_texts',
    'validate_images',
    'validate_texts'
]

RENDER_DIR = '_rendered'
DEFAULT_NUM_DOCS = 500
IMG_HEIGHT = 224
IMG_WIDTH = 224
FILE_PREFIX = 'stats'
TOP_K = os.environ.get('TOP_K')
FLOW_HOST = os.environ.get('FLOW_HOST')
FLOW_PORT_GRPC = 45678

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
        yield doc


def random_texts(num_docs):
    for idx in range(num_docs):
        with Document() as doc:
            doc.text = random_sentences(random.randint(1, 20))
            doc.tags['filename'] = f'filename {idx}'
            num_chunks = random.randint(1, 10)
            for _ in range(num_chunks):
                doc.text += '. ' + random_sentences(random.randint(1, 20))
        yield doc


def _log_time_per_pod(routes):
    time_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    time_per_pod = {
        i['pod']: (datetime.strptime(i['endTime'], time_fmt) -
                   datetime.strptime(i['startTime'], time_fmt)).total_seconds() * 1000
        for i in routes
    }
    logger.info(time_per_pod)


def validate_images(resp, top_k):
    _log_time_per_pod(resp.dict()['routes'][:-1])
    for d in resp.search.docs:
        if len(d.matches) != top_k:
            logger.error(f' MATCHES LENGTH IS NOT TOP_K {top_k} but {len(d.matches)}')
        for m in d.matches:
            if 'filename' not in m.tags.keys():
                logger.error(f'filename not in tags: {m.tags}')
            # to test that the data from the KV store is retrieved
            if 'image ' not in m.tags['filename']:
                logger.error(f'"image" not in m.tags["filename"]: {m.tags["filename"]}')
        # assert len(d.matches) == TOP_K, f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}'


def validate_texts(resp):
    _log_time_per_pod(resp.dict()['routes'][:-1])
    logger.info(f'got {len(resp.search.docs)} docs in resp.search')
    for d in resp.search.docs:
        if len(d.matches) != TOP_K:
            logger.error(f'Number of actual matches: {len(d.matches)} vs expected number: {TOP_K}')
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
