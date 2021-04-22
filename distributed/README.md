# Distributed Stress Tests

---------------------------

## [settings.yaml](./settings.yaml)

1. Define a `stress-test` job under `jobs` & `steps` under each job.

1. Each step needs a `method`.
   [Allowed methods -](./steps.py)

   - create_workspace
   - update_workspace
   - delete_workspace
   - start_flow
   - terminate_flow
   - index
   - query

1. Each method accepts a set of kwargs (according to function definition in steps).
   Points to note -

    - `create_workspace` and `update_workspace`
      - `files`: pod yaml/py_modules to upload to JinaD.
      - `environment`: replace env variables in yaml files

    - `index` and `query` arguments:
      - `execution_time`: run index/query for secs
      - `inputs`: accepts a method name (data ingester). we can pass `kwargs` which are args for the data ingester method.
      - `on_always`: accepts a method name (data validator/metric logger). we can pass `kwargs` which are args for the data validator method.
      - `request_size`: request size for index/query
      - `gateway_host`: flow gateway IP (default: localhost)
      - `gateway_port`: flow gateway port (default: 23456)
      - `client`: `grpc` or `websockets` (pass according to flow gateway)
      - `num_clients`: number of concurrent clients (TODO)
      - `top_k`: available for query only

    - `sleep_time` can be passed with any step to sleep before execution.

1. Worry only about jina specific things:

   - `flow/pod yaml`
   - `inputs`
   - `on_always`

##### TODO:

- [ ] Multiple clients (code exists, needs refactoring)
- [ ] Consume host env vars from `jina-terraform/custom-jinad-deployment`
- [ ] Log metrics (what & how)
  - [X] Time spent at each pod for each request (info available with response). This can help us determine time for indexing/encoding/querying/ranking etc.
  - [ ] Number of docs per sec / QPS
  - [ ] System metrics using cloudwatch (@niuzs-alan)
- [ ] Upload metrics to S3 (should be a new `step`)
- [ ] Send metrics update to Slack (shoule be a new `step`)
- [ ] Currently we index random images/text. Should move to a "good" dataset.

---------------------------

### Run locally or, on cloud

```bash
# Start JinaD on local/cloud
# Edit settings.yaml & set env vars during `create_workspace` for host details.
# For local, use images/index_local.yml / images/query_local.yml.
pip install -r requirements.txt
python trigger.py
```
