import glob
from pathlib import Path

from logger import logger
from .client import AWSClient


class S3:
    """Wrapper around boto3 to upload to/download from S3 bucket
    """

    def __init__(self, bucket: str):
        self._client = AWSClient(service='s3').client
        self._bucket = bucket

    def add(self, path: str, key: str):
        if not Path(path).exists():
            logger.error(f'Invalid path: {path}! Nothing to upload!')
            return
        try:
            logger.info(f'Uploading object from `{path}` to S3 bucket `{self._bucket}` key `{key}`')
            for filename in glob.iglob(str(path) + '**/**', recursive=True):
                if Path(filename).is_file():
                    self._client.upload_file(filename, self._bucket, f'{key}/{filename}')
        except Exception as exp:
            logger.error(f'Got following exception while uploading object to S3 \n{exp}')
            raise

    def get(self, key: str, local_path):
        try:
            logger.info(f'Downloading object from `{self._bucket}:{key}` to file: {local_path}')
            self._client.download_file(self._bucket, key, local_path)
        except Exception as exp:
            logger.error(f'Got following exception while downloading object from S3 \n{exp}')
            raise
