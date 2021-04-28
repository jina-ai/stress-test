import os
import boto3

from logger import logger


class AWSClient:
    """Wrapper around boto3 to create aws clients
    """

    def __init__(self, service: str, region: str = 'us-east-2'):
        self._service = service
        self._region = region
        if all(len(os.getenv(k, '')) > 0 for k in ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY')):
            self._client = boto3.client(service_name=self._service,
                                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                        region_name=self._region)
        else:
            raise EnvironmentError(f'Please set AWS related env vars')

    @property
    def client(self):
        return self._client

    @property
    def all_waiters(self):
        return self._client.waiter_names

    @property
    def waiter(self):
        return self._waiter

    @waiter.setter
    def waiter(self, waiter_name):
        try:
            if waiter_name not in self.all_waiters:
                logger.error(f'Invalid waiter `{waiter_name} for service `{self._service}`')
            self._waiter = self.client.get_waiter(waiter_name=waiter_name)
        except Exception as exp:
            logger.exception(f'Got the following exception while getting the waiter {exp}')
            raise
