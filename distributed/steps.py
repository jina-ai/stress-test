import uuid
from typing import List, Dict, Callable, ClassVar
from pydantic import validate_arguments, FilePath
from pydantic.types import DirectoryPath

import data
import control
from aws import S3
from helper import set_environment_vars, GatewayClients


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
        set_environment_vars(files=files, environment=environment)
        StepItems.workspace = control.create_or_update_workspace(files=files)

    @classmethod
    @validate_arguments
    def update_workspace(cls,
                         *,
                         files: List[FilePath],
                         environment: Dict[str, str]):
        set_environment_vars(files=files, environment=environment)
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
              gateway_host: str = 'localhost',
              gateway_port: int = 23456,
              client: GatewayClients = GatewayClients.GRPC,
              num_clients: int = 1,
              request_size: int = 100,
              execution_time: int = 10):
        data.index(inputs=inputs,
                   inputs_args=inputs_args,
                   on_always=on_always,
                   on_always_args=on_always_args,
                   gateway_host=gateway_host,
                   gateway_port=gateway_port,
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
              gateway_host: str = 'localhost',
              gateway_port: int = 23456,
              client: GatewayClients = GatewayClients.GRPC,
              num_clients: int = 1,
              request_size: int = 100,
              top_k: int = 50,
              execution_time: int = 10):
        data.query(inputs=inputs,
                   inputs_args=inputs_args,
                   on_always=on_always,
                   on_always_args=on_always_args,
                   gateway_host=gateway_host,
                   gateway_port=gateway_port,
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
        S3(bucket=bucket).add(path=directory, key=str(uuid.uuid4()))

    @classmethod
    @validate_arguments
    def download_from_s3(cls,
                         *,
                         key: str,
                         local_directory: str = '.',
                         bucket: str = 'e2e-distributed-stress-tests'):
        S3(bucket=bucket).get(key=key, local_directory=local_directory)
