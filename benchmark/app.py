import os
import time
import uuid
from math import ceil

import click
from pandas import DataFrame

from jina.flow import Flow
from jina.drivers import BaseDriver

from post_process import clean_dataframe, evaluate_times, get_summary
from utils import bytes_generator, generate_filename, get_list_of_num_docs
from summary import html_table, plot_num_docs_vs_time

FILE_DIR = os.environ.get('FILE_DIR', './.data')
os.makedirs(FILE_DIR, exist_ok=True)

START_NUM_DOCS = 512
MULTIPLIER_NUM_DOCS = 4
COUNT_NUM_DOCS = 10
DEFAULT_BATCH_SIZE = 256
COLUMN_OF_INTEREST = 'g:send' # to be changed to 'roundtrip' once issue is fixed


class BenchmarkDriver(BaseDriver):
    routes = []

    def __init__(self, num_pods: str = '2', num_epochs: str = '2', filename: str = 'routes.parquet', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_pods = int(num_pods)
        self.num_epochs = int(num_epochs)
        self.filename = filename

    def __call__(self, *args, **kwargs):
        if (len(self.envelope.routes) == self.num_pods + 1) and (len(self.req.docs) > 0):
            # 1st condition is to make sure we extract `routes` only at the last pod
            # 2nd condition is to make sure we don't write to the file during dry_run
            current_route_dict = {}
            for _pod in self.envelope.routes:
                name = _pod.pod
                start_time = _pod.start_time.ToDatetime()
                end_time = _pod.end_time.ToDatetime()
                current_route_dict[name] = [start_time, end_time]
            BenchmarkDriver.routes.append(current_route_dict)
            if len(BenchmarkDriver.routes) == self.num_epochs:
                DataFrame(BenchmarkDriver.routes).to_parquet(f'{FILE_DIR}/{self.filename}')


@click.command()
@click.option('--num-bytes', '-b', default=10)
@click.option('--num-pods', default=2)
@click.option('--batch-size', default=DEFAULT_BATCH_SIZE)
def run_benchmark(num_bytes, num_pods, batch_size):
    overall_summary = {}

    for num_docs in get_list_of_num_docs(start=START_NUM_DOCS, 
                                         multiplier=MULTIPLIER_NUM_DOCS, 
                                         count=COUNT_NUM_DOCS):
        num_epochs = ceil(num_docs / batch_size)
        filename = generate_filename(num_docs, num_bytes)

        os.environ['num_pods'] = str(num_pods)
        os.environ['filename'] = filename
        os.environ['num_epochs'] = str(num_epochs)
        
        f = Flow()
        for _ in range(num_pods):
            f = f.add(uses='benchmark.yml') # change path
        with f:  
            f.index(input_fn=bytes_generator(num_docs=num_docs, num_bytes=num_bytes), 
                    batch_size=batch_size)
        time.sleep(1)
        routes_df = clean_dataframe(filepath=f'{FILE_DIR}/{filename}')
        routes_df, columns_of_interest = evaluate_times(routes_df=routes_df, num_docs=num_docs, num_pods=num_pods)
        current_summary = get_summary(routes_df=routes_df, columns_of_interest=columns_of_interest)
        overall_summary[num_docs] = current_summary
        os.remove(f'{FILE_DIR}/{filename}')
    
    print(overall_summary)
    html_table_text = html_table(overall_summary_dict=overall_summary)
    uuid_gen = uuid.uuid4().hex.lower()[0:10]
    image_filename = plot_num_docs_vs_time(overall_summary_dict=overall_summary,
                                           column_of_interest=COLUMN_OF_INTEREST, 
                                           uid=uuid_gen) # to be changed to gh hash
    with open('README.MD', 'w') as readme_f:
        readme_f.write('<h3>Results</h3>')
        readme_f.write(html_table_text)
        readme_f.write('\n\n\n<h3>Num docs vs Time<h3>\n\n')
        readme_f.write(f'![Num docs vs Time]({image_filename})')


if __name__ == '__main__':
    run_benchmark()
