<h1> Benchmark Flows </h1>

Use this to benchmark latencies across different pods.
- Add index yaml in `yamls` folder, pod yamls to the `yamls/pods` folder.
- Takes care of adding `benchmark_driver.yml` pod at the end which determines `start_time` & `end_time` for each pod.
- Supports indexing & querying random `bytes` or `jina_pb2.Document` or `sentences` (to be added). Custom `input_fn` can be added.

