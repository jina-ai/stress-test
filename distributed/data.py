import os
import time
from functools import partial
from multiprocessing import Pool
from typing import Dict, Callable

from jina.parsers import set_client_cli_parser
from jina.clients import Client, WebSocketClient
from pydantic import validate_arguments

from logger import logger
from helper import GatewayClients, Tasks


def _fetch_client(client: GatewayClients):
    gateway_data_host = f'{os.getenv("JINA_GATEWAY_HOST") if os.getenv("JINA_GATEWAY_HOST") else "localhost"}'
    gateway_data_port = f'{os.getenv("JINA_GATEWAY_PORT_EXPOSE") if os.getenv("JINA_GATEWAY_PORT_EXPOSE") else "23456"}'
    args = set_client_cli_parser().parse_args(['--host', gateway_data_host, '--port-expose', str(gateway_data_port)])
    return Client(args) if client == GatewayClients.GRPC else WebSocketClient(args)


def _trigger(task: Tasks, client: GatewayClients, execution_time: float, inputs: Callable,
             inputs_args: Dict, request_size: int, on_always: Callable, on_always_args: Dict, top_k: int = 10):
    run_until = time.time() + execution_time
    client = _fetch_client(client=client)
    while time.time() < run_until:
        try:
            if task == Tasks.INDEX:
                client.index(
                    inputs(**inputs_args),
                    request_size=request_size,
                    on_always=partial(on_always, **on_always_args)
                )
            elif task == Tasks.SEARCH:
                client.search(
                    inputs(**inputs_args),
                    request_size=request_size,
                    top_k=top_k,
                    on_always=partial(on_always, **on_always_args)
                )
        except ZeroDivisionError:
            logger.error(f'ZeroDivisionError: seems to be an issue with profile logger, ignoring for now.')
            continue


def _handle_clients(num_clients, *args):
    with Pool(num_clients) as pool:
        results = [pool.apply_async(_trigger, args=args) for _ in range(num_clients)]
        [r.get() for r in results]


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
    logger.info(f'👍 Starting indexing for {execution_time} secs')
    on_always_args.update({'client': client.value})
    _handle_clients(num_clients, 'index', client, execution_time, inputs,
                    inputs_args, request_size, on_always, on_always_args)


@validate_arguments
def query(*,
          inputs: Callable,
          inputs_args: Dict,
          on_always: Callable,
          on_always_args: Dict = {},
          client: GatewayClients = 'grpc',
          num_clients: int = 1,
          request_size: int = 100,
          execution_time: int = 10,
          top_k: int = 10):
    logger.info(f'👍 Starting querying for {execution_time} secs')
    on_always_args.update({'top_k': top_k, 'client': client.value})
    _handle_clients(num_clients, 'search', client, execution_time, inputs,
                    inputs_args, request_size, on_always, on_always_args, top_k)
