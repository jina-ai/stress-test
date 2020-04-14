import os
import time

from jina.enums import SchedulerType
from jina.executors.crafters import BaseDocCrafter
from jina.flow import Flow


class SlowWorker(BaseDocCrafter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # half of worker is slow
        self.is_slow = os.getpid() % 10 != 0
        self.logger.warning('im a slow worker')

    def craft(self, doc_id, *args, **kwargs):
        if self.is_slow:
            self.logger.warning('slowly doing')
            time.sleep(2)
        return {'doc_id': doc_id}


if __name__ == '__main__':
    from slow_worker import random_docs

    f = Flow(runtime='process', logserver=True, logserver_config='test-server-config.yml').add(name='sw',
                                                                                               yaml_path='SlowWorker',
                                                                                               replicas=20,
                                                                                               scheduling=SchedulerType.LOAD_BALANCE).build()

    with f:
        f.index(raw_bytes=random_docs(1000), in_proto=True, batch_size=10)
