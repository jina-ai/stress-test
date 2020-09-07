<h1> Benchmark Flows </h1>

Use this to benchmark latencies across different pods.
- Add index yaml in `yamls` folder, pod yamls to the `yamls/pods` folder.
- Takes care of adding `benchmark_driver.yml` pod at the end which determines `start_time` & `end_time` for each pod.
- Supports indexing & querying random `bytes` or `jina_pb2.Document` or `sentences` (to be added). Custom `input_fn` can be added.
- Get benchmarks for different indexing of different #of documents.



<h3> Environment Variables </h3>


```
START_NUM_DOCS - #of documents to start the benchmark with (Default - 2**15)
MULTIPLIER_NUM_DOCS - repetitive multiplcation number from START_NUM_DOCS (Default -2)
COUNT_NUM_DOCS - #of experiments to peform (Default - 5)
e.g.- For START_NUM_DOCS=512, MULTIPLIER_NUM_DOCS=4, COUNT_NUM_DOCS=4, we'll run experiments for [512, 2048, 8192, 32768]

BATCH_SIZE - #of documents per batch (Default - 256)
EMBED_DIM - Dimension for Embedding in jina_pb2.Document (Default - 16)
FILE_DIR - Directory where parquet file & plots will be stored (Default - .data)
```
