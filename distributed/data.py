import time
from functools import partial
from typing import Dict, Callable

from jina.clients import Client, WebSocketClient
from jina.parsers import set_client_cli_parser
from pydantic import validate_arguments

from logger import logger
from helper import GatewayClients


def _fetch_client(client: GatewayClients, gateway_host: str, gateway_port: int):
    args = set_client_cli_parser().parse_args(['--host', gateway_host, '--port-expose', str(gateway_port)])
    return Client(args) if client == GatewayClients.GRPC else WebSocketClient(args)


@validate_arguments
def index(*,
          inputs: Callable,
          inputs_args: Dict,
          on_always: Callable,
          on_always_args: Dict = {},
          gateway_host: str = 'localhost',
          gateway_port: int = 23456,
          client: GatewayClients = 'grpc',
          num_clients: int = 1,
          request_size: int = 100,
          execution_time: int = 10):
    # TODO: add support for multiple clients
    logger.info(f'👍 Starting indexing for {execution_time} secs')
    run_until = time.time() + execution_time
    client = _fetch_client(client=client,
                           gateway_host=gateway_host,
                           gateway_port=gateway_port)
    on_always_args.update({'task': 'index'})
    while time.time() < run_until:
        client.index(inputs(**inputs_args),
                     request_size=request_size,
                     on_always=partial(on_always, **on_always_args))


@validate_arguments
def query(*,
          inputs: Callable,
          inputs_args: Dict,
          on_always: Callable,
          on_always_args: Dict = {},
          gateway_host: str = 'localhost',
          gateway_port: int = 23456,
          client: GatewayClients = 'grpc',
          execution_time: int = 10,
          num_clients: int = 1,
          request_size: int = 100,
          top_k: int = 10):
    # TODO: add support for multiple clients
    logger.info(f'👍 Starting querying for {execution_time} secs')
    run_until = time.time() + execution_time
    client = _fetch_client(client=client,
                           gateway_host=gateway_host,
                           gateway_port=gateway_port)
    on_always_args.update({'top_k': top_k, 'task': 'query'})
    while time.time() < run_until:
        client.search(inputs(**inputs_args),
                      request_size=request_size,
                      top_k=top_k,
                      on_always=partial(on_always, **on_always_args))
