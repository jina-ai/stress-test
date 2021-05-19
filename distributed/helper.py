import csv
import itertools
import os
import json
import shutil
import sys
import time
import random
from enum import Enum
from pathlib import Path
from shutil import copyfile
from typing import Dict, List
from datetime import datetime

import requests
import yaml
import chevron
import numpy as np
from jina import Document, Request
from jinacld_tools.aws.services.s3 import S3Bucket
from pydantic import FilePath, validate_arguments

from logger import logger

LOGGERS = {}
RENDER_DIR = '_rendered'
IMG_HEIGHT = 224
IMG_WIDTH = 224
SUPPORTED_IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.gif')

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


class GatewayClients(str, Enum):
    GRPC = 'grpc'
    WEBSOCKET = 'websocket'


class Tasks(str, Enum):
    INDEX = 'index'
    SEARCH = 'search'


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


def dataset_images(dataset_path: str, num_docs: int = 100):
    from steps import StepItems
    from PIL import Image

    ds_image_state_key = f'ds_image_{dataset_path}'
    if ds_image_state_key not in StepItems.state:
        StepItems.state[ds_image_state_key] = os.scandir(dataset_path)
    files = StepItems.state[ds_image_state_key]

    for file in itertools.islice(files, num_docs):
        if file.is_file() and Path(file.path).suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
            with Document() as doc:
                img = Image.open(file.path)
                doc.content = np.array(img)
                doc.mime_type = img.get_format_mimetype()
                doc.tags['filename'] = file.name
            yield doc


def wikipedia_docs(dataset_path: str, num_docs: int = 100):
    from steps import StepItems

    ds_wiki_state_key = f'ds_wiki_{dataset_path}'
    if ds_wiki_state_key not in StepItems.state:
        StepItems.state[ds_wiki_state_key] = open(dataset_path, newline='', encoding='utf-8')
    reader = StepItems.state[ds_wiki_state_key]

    doc_count = 0
    current_doc = None
    for line in reader:
        if doc_count >= num_docs:
            return

        if line.startswith('<doc>'):
            current_doc = _create_empty_doc(current_doc)
        elif line.startswith('</doc>'):
            yield current_doc
            current_doc = None
            doc_count += 1
        elif line.startswith('<title>'):
            # format is <title>Wikipedia: Apollo</title>
            if current_doc is None:
                current_doc = _create_empty_doc(current_doc)
            current_doc.tags['title'] = line[line.index('>')+1:line.index('</')].replace("Wikipedia: ", "")
        elif line.startswith('<abstract>'):
            # format is <title>Wikipedia: Apollo</title>
            if current_doc is None:
                current_doc = _create_empty_doc(current_doc)
            current_doc.text = line[line.index('>')+1:line.index('</')].replace("Wikipedia: ", "")


def _create_empty_doc(current_doc):
    current_doc = Document()
    current_doc.tags['timestamp'] = str(time.time())
    return current_doc


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
                      num_docs: int = 0,
                      **kwargs):
    global LOGGERS

    from logger import get_logger
    pid = os.getpid()
    if f'p2p_pid_{pid}' not in LOGGERS:
        LOGGERS[f'p2p_pid_{pid}'] = get_logger(context=f'p2p_pid_{pid}')

    p2p_metrics_logger = LOGGERS[f'p2p_pid_{pid}']
    state[f'{task}_doc_counter'] = num_docs if f'{task}_doc_counter' not in state \
        else state[f'{task}_doc_counter'] + num_docs

    def _time_diff_ms(start, end):
        _time_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
        # all times logged in ms
        return (datetime.strptime(end, _time_fmt) - datetime.strptime(start, _time_fmt)).total_seconds() * 1000

    time_per_pod = {i['pod']: f'{_time_diff_ms(i["start_time"], i["end_time"]):.0f}' for i in routes if 'end_time' in i}
    p2p_metrics_logger.info(json.dumps(
        {'task': task,
         'process_id': pid,
         'num_jina_docs': num_docs,
         'cumulative_num_jina_docs': state[f'{task}_doc_counter'],
         **kwargs,
         'client_roundtrip': f'{(time.time() - timestamp) * 1000:.0f}',
         **time_per_pod}
    ))


def validate_images(resp: Request, top_k: int = 10, **kwargs):
    try:
        from steps import StepItems
        resp_dict = resp.dict()
        task = 'index' if 'index' in resp_dict.keys() else 'search'
        timestamp_from_tags = np.mean([float(doc['tags']['timestamp']) for doc in resp_dict[task]['docs']])
        _log_time_per_pod(routes=resp_dict['routes'],
                          timestamp=timestamp_from_tags,
                          state=StepItems.state,
                          task=task,
                          num_docs=len(resp_dict[task]['docs']), **kwargs)
        for d in resp.search.docs:
            if len(d.matches) != top_k:
                logger.error(f'Number of actual matches: {len(d.matches)} vs expected number: {top_k}')
            for m in d.matches:
                if 'timestamp' not in m.tags.keys():
                    logger.error(f'timestamp not in tags: {m.tags}')
                if 'filename' not in m.tags.keys():
                    logger.error(f'filename not in tags: {m.tags}')
                # to test that the data from the KV store is retrieved
                if 'image ' not in m.tags['filename']:
                    logger.error(f'"image" not in m.tags["filename"]: {m.tags["filename"]}')
    except Exception as e:
        logger.exception(f'Got an exception during `validate_images`. Continuing (not raising)')


def validate_texts(resp: Request, top_k: int = 10, **kwargs):
    try:
        from steps import StepItems
        resp_dict = resp.dict()
        task = 'index' if 'index' in resp_dict.keys() else 'search'
        timestamp_from_tags = float(resp_dict[task]['docs'][0]['tags']['timestamp'])
        _log_time_per_pod(routes=resp_dict['routes'],
                          timestamp=timestamp_from_tags,
                          state=StepItems.state,
                          task=task,
                          num_docs=len(resp_dict[task]['docs']), **kwargs)

        for d in resp.search.docs:
            if len(d.matches) != top_k:
                logger.error(f'Number of actual matches: {len(d.matches)} vs expected number: {top_k}')
            for m in d.matches:
                if 'timestamp' not in m.tags.keys():
                    logger.error(f'timestamp not in tags: {m.tags}')
                # to test that the data from the KV store is retrieved
                if 'filename' not in m.tags.keys():
                    logger.error(f'did not find "filename" in tags: {m.tags}')
    except Exception as e:
        logger.exception(f'Got an exception during `validate_images`. Continuing (not raising)')


@validate_arguments
def update_environment_vars(files: List[FilePath], environment: Dict[str, str]):
    update_instances_environment_vars(environment=environment)
    set_os_environment_vars(environment=environment)
    os.makedirs(RENDER_DIR, exist_ok=True)
    for file in files:
        copyfile(file, f'{RENDER_DIR}/{file.name}')
        with open(file, 'r') as org_file, open(f'{RENDER_DIR}/{file.name}', 'w') as rendered_file:
            content_to_be_rendered = chevron.render(org_file, environment)
            rendered_file.write(content_to_be_rendered)


def set_os_environment_vars(environment: Dict[str, str]):
    for k, v in environment.items():
        os.environ[k] = str(v)


def update_instances_environment_vars(environment: Dict[str, str]):
    if Path('instances.yaml').is_file():
        with open('instances.yaml') as f:
            host_env = yaml.safe_load(f)
            if 'instances' in host_env:
                environment.update(host_env['instances'])


def terminate_test():
    if 'GITHUB_TOKEN' not in os.environ:
        logger.warning('Not terminating stress test, no github token provided')
        return
    if 'TFID' not in os.environ:
        logger.warning('Not terminating stress test, no tfid provided')
        return
    if 'STRESS_TEST_TEST_NAME' not in os.environ:
        logger.warning('Not terminating stress test, no test name provided')
        return

    logger.info(f'Terminating stress test {os.environ["TFID"]} with type {os.environ["STRESS_TEST_TEST_NAME"]}')
    resp = requests.post('https://api.github.com/repos/jina-ai/jina-terraform/dispatches',
                  headers={'Accept': 'application/vnd.github.v3+json',
                           'Authorization': f'token {os.environ["GITHUB_TOKEN"]}'},
                  json={'event_type': 'terminate-stress-test',
                        'client_payload': {'tfid:': os.environ["TFID"],
                                           'test-name': os.environ["STRESS_TEST_TEST_NAME"]}})
    logger.info(f'Terminating stress test response is {resp.status_code}')
