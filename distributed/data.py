import time
from functools import partial
from typing import Dict, Callable

from jina.clients import Client, WebSocketClient
from jina.parsers import set_client_cli_parser
from pydantic import validate_arguments

from logger import logger
from helper import GatewayClients


FLOW_PORT_GRPC = 23456
FLOW_PROTO = 'http'
FLOW_HOST = 'localhost'
FLOW_PORT = 8000
FLOW_HOST_PORT = f'{FLOW_PROTO}://{FLOW_HOST}:{FLOW_PORT}'


def _fetch_client(client: GatewayClients):
    args = set_client_cli_parser().parse_args(['--host', FLOW_HOST, '--port-expose', str(FLOW_PORT_GRPC)])
    return Client(args) if client == GatewayClients.GRPC else WebSocketClient(args)


@validate_arguments
def index(*,
          inputs: Callable,
          inputs_args: Dict,
          on_always: Callable,
          on_always_args: Dict = {},
          client: GatewayClients = 'grpc',
          num_clients: int = 1,
          request_size: int = 100,
          execution_time: int = 10):
    # TODO: add support for multiple clients
    logger.info(f'👍 Starting indexing for {execution_time} secs')
    run_until = time.time() + execution_time
    while time.time() < run_until:
        if on_always_args:
            _fetch_client(client=client).index(inputs(**inputs_args),
                                               request_size=request_size,
                                               on_always=partial(on_always, **on_always_args))
        else:
            _fetch_client(client=client).index(inputs(**inputs_args),
                                               request_size=request_size,
                                               on_always=on_always)


@validate_arguments
def query(*,
          inputs: Callable,
          inputs_args: Dict,
          on_always: Callable,
          on_always_args: Dict = {},
          client: GatewayClients = 'grpc',
          execution_time: int = 10,
          num_clients: int = 1,
          request_size: int = 100):
    # TODO: add support for multiple clients
    logger.info(f'👍 Starting querying for {execution_time} secs')
    run_until = time.time() + execution_time
    while time.time() < run_until:
        if on_always_args:
            _fetch_client(client=client).search(inputs(**inputs_args),
                                                request_size=request_size,
                                                on_always=partial(on_always, **on_always_args))
        else:
            _fetch_client(client=client).search(inputs(**inputs_args),
                                                request_size=request_size,
                                                on_always=on_always)
