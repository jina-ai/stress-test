import os
import uuid
from typing import List, Dict, Callable, ClassVar

import requests
from pydantic import validate_arguments, FilePath
from pydantic.types import DirectoryPath

import data
import control
from aws import S3
from stats import collect_and_push
from helper import update_environment_vars, GatewayClients


class StepItems:
    workspace: ClassVar[uuid.uuid4] = None
    flow: ClassVar[uuid.uuid4] = None
    state: ClassVar[Dict] = {}

    @classmethod
    @validate_arguments
    def create_workspace(cls,
                         *,
                         files: List[FilePath],
                         environment: Dict[str, str]):
        update_environment_vars(files=files, environment=environment)
        StepItems.workspace = control.create_or_update_workspace(files=files)

    @classmethod
    @validate_arguments
    def update_workspace(cls,
                         *,
                         files: List[FilePath],
                         environment: Dict[str, str]):
        update_environment_vars(files=files, environment=environment)
        StepItems.workspace = control.create_or_update_workspace(files=files,
                                                                 workspace_id=StepItems.workspace)

    @classmethod
    @validate_arguments
    def delete_workspace(cls):
        control.delete_workspace(workspace_id=StepItems.workspace)
        StepItems.workspace = None

    @classmethod
    @validate_arguments
    def start_flow(cls,
                   *,
                   file: FilePath):
        StepItems.flow = control.start_flow(file=file,
                                            workspace_id=StepItems.workspace)

    @classmethod
    @validate_arguments
    def terminate_flow(cls):
        control.terminate_flow(flow_id=StepItems.flow,
                               delete_workspace=False)
        StepItems.flow = None

    @classmethod
    @validate_arguments
    def index(cls,
              *,
              inputs: Callable,
              inputs_args: Dict,
              on_always: Callable,
              on_always_args: Dict = {},
              client: GatewayClients = GatewayClients.GRPC,
              num_clients: int = 1,
              request_size: int = 100,
              execution_time: int = 10):
        data.index(inputs=inputs,
                   inputs_args=inputs_args,
                   on_always=on_always,
                   on_always_args=on_always_args,
                   client=client,
                   execution_time=execution_time,
                   num_clients=num_clients,
                   request_size=request_size)

    @classmethod
    @validate_arguments
    def query(cls,
              *,
              inputs: Callable,
              inputs_args: Dict,
              on_always: Callable,
              on_always_args: Dict = {},
              client: GatewayClients = GatewayClients.GRPC,
              num_clients: int = 1,
              request_size: int = 100,
              execution_time: int = 10,
              top_k: int = 10):
        data.query(inputs=inputs,
                   inputs_args=inputs_args,
                   on_always=on_always,
                   on_always_args=on_always_args,
                   client=client,
                   execution_time=execution_time,
                   num_clients=num_clients,
                   request_size=request_size,
                   top_k=top_k)

    @classmethod
    @validate_arguments
    def upload_to_s3(cls,
                     *,
                     directory: DirectoryPath,
                     bucket: str = 'e2e-distributed-stress-tests'):
        s3_key = os.getenv('TFID') if 'TFID' in os.environ else str(uuid.uuid4())
        S3(bucket=bucket).add(path=directory, key=s3_key)

    @classmethod
    @validate_arguments
    def download_from_s3(cls,
                         *,
                         key: str,
                         local_directory: str = '.',
                         bucket: str = 'e2e-distributed-stress-tests'):
        S3(bucket=bucket).get(key=key, local_path=f'{local_directory}/{key}')

    @classmethod
    @validate_arguments
    def collect_stats(cls,
                      *,
                      slack: bool = False):
        collect_and_push(slack=slack)

    @classmethod
    @validate_arguments
    def download_and_extract_from_web(cls,
                                      *,
                                      uri: str,
                                      format: str = None):
        import shutil

        file_name = f'./{os.path.basename(uri)}'
        if not os.path.exists(file_name):
            resp = requests.get(uri)
            if resp.status_code != 200:
                raise FileNotFoundError(f'Could not download data from {uri}')
            else:
                with open(file_name, 'wb') as f:
                    f.write(resp.content)
                shutil.unpack_archive(file_name, format=format)

    @classmethod
    @validate_arguments
    def terminate_test(cls):

        if 'GITHUB_TOKEN' not in os.environ:
            raise ValueError('Can not terminate test, GITHUB_TOKEN not a enverionment variable')
        if 'TFID' not in os.environ:
            raise ValueError('Can not terminate test, TFID not a enverionment variable')
        if 'STRESS_TEST_TEST_NAME' not in os.environ:
            raise ValueError('Can not terminate test, STRESS_TEST_TEST_NAME not a enverionment variable')

    requests.post('https://api.github.com/repos/jina-ai/jina-terraform/dispatches',
                  headers={'Accept': 'application/vnd.github.v3+json',
                           'Authorization': f'token {os.environ["GITHUB_TOKEN"]}'},
                  json={'event_type': 'terminate-stress-test',
                        'client_payload': {'tfid:': os.environ["TFID"],
                                           'test-name': os.environ["STRESS_TEST_TEST_NAME"]}})
