import uuid
from typing import List
from contextlib import ExitStack

import requests
from pydantic import FilePath, UUID4

from logger import logger
from helper import RENDER_DIR

FLOW_PROTO = 'http'
FLOW_HOST = 'localhost'
FLOW_PORT = 8000
FLOW_HOST_PORT = f'{FLOW_PROTO}://{FLOW_HOST}:{FLOW_PORT}'

if FLOW_PROTO is None or FLOW_HOST is None or FLOW_PORT is None:
    raise ValueError(f'Make sure you set all of FLOW_PROTO, FLOW_HOST, FLOW_PORT. Current url = {FLOW_HOST_PORT}')


def create_or_update_workspace(*,
                               files: List[FilePath],
                               url: str = f'{FLOW_HOST_PORT}/workspaces',
                               workspace_id: UUID4 = None) -> UUID4:
    with ExitStack() as file_stack:
        files = [
            ('files', file_stack.enter_context(open(f'{RENDER_DIR}/{file.name}', 'rb')))
            for file in files
        ]
        logger.debug(f'Creating a workspace to upload files: {files}')

        if workspace_id:
            r = requests.post(url=url,
                              data={'workspace_id': workspace_id},
                              files=files)
        else:
            r = requests.post(url=url, files=files)

        if r.status_code != requests.codes.created:
            logger.critical(f'❌ Workspace creation failed with status {r.status_code}. Response: {r.json()}')
            r.raise_for_status()

        workspace_id = r.json()
        logger.info(f'💪 Successfully uploaded files to workspace: {workspace_id}')
        return uuid.UUID(workspace_id)


def delete_workspace(*,
                     workspace_id: UUID4,
                     url: str = f'{FLOW_HOST_PORT}/workspaces'):
    r = requests.delete(url=f'{url}/{workspace_id}')

    if r.status_code != requests.codes.ok:
        logger.critical(f'❌ Workspace deletion failed with status {r.status_code}. Response: {r.json()}')
        r.raise_for_status()
    logger.info(f'💪 Successfully deleted workspace {workspace_id}')


def start_flow(*,
               file: FilePath,
               workspace_id: uuid.uuid4,
               url: str = f'{FLOW_HOST_PORT}/flows') -> UUID4:
    with open(f'{RENDER_DIR}/{file.name}', 'rb') as f:
        r = requests.post(url=url,
                          data={'workspace_id': workspace_id},
                          files={'flow': f})

        if r.status_code != requests.codes.created:
            logger.critical(f'❌ Flow start failed with status {r.status_code}. Response: {r.json()}')
            r.raise_for_status()

        flow_id = r.json()
        logger.info(f'💪 Successfully created a flow: {flow_id}')
        return uuid.UUID(flow_id)


def terminate_flow(*,
                   flow_id: UUID4,
                   url: str = f'{FLOW_HOST_PORT}/flows',
                   delete_workspace: bool = False):
    r = requests.delete(url=f'{url}/{flow_id}',
                        json={'workspace': delete_workspace})

    if r.status_code != requests.codes.ok:
        logger.critical(f'❌ Flow termination failed with status {r.status_code}. Response: {r.json()}')
        r.raise_for_status()
    logger.info(f'💪 Successfully terminated flow {flow_id}')
