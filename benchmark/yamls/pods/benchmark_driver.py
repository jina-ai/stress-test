from jina.drivers import BaseDriver
from pandas import DataFrame


class BenchmarkDriver(BaseDriver):
    routes = []
    def __init__(self, num_epochs, file_path: str = 'routes.parquet', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_epochs = int(num_epochs)
        self.file_path = file_path
        self._prev_envelopes = []

    def __call__(self, *args, **kwargs):  
        if len(self.req.docs) > 0:
            self._prev_envelopes.append(self.envelope)
            if len(self._prev_envelopes) == self.num_epochs:
                for envelope in self._prev_envelopes:
                    current_route_dict = {}
                    for _pod in envelope.routes:
                        name = _pod.pod
                        start_time = _pod.start_time.ToDatetime()
                        end_time = _pod.end_time.ToDatetime()
                        current_route_dict[name] = [start_time, end_time]
                    BenchmarkDriver.routes.append(current_route_dict)
                DataFrame(BenchmarkDriver.routes).to_parquet(self.file_path)

