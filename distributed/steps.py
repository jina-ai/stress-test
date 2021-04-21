import uuid
from typing import List, Dict, Callable, ClassVar
from pydantic import validate_arguments, FilePath

import data
import control
from logger import logger
from helper import set_environment_vars, GatewayClients


class StepItems:
    workspace: ClassVar[uuid.uuid4] = None
    flow: ClassVar[uuid.uuid4] = None

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
              execution_time: int = 10):
        data.query(inputs=inputs,
                   inputs_args=inputs_args,
                   on_always=on_always,
                   on_always_args=on_always_args,
                   client=client,
                   execution_time=execution_time,
                   num_clients=num_clients,
                   request_size=request_size)
