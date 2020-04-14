# Stress Test

A collection of stress tests of Jina infrastructure


## Case 1: Slow Worker for Testing Load Balancing

To test `--scheduling`

[slow_worker](slow_worker/app.py)


## Case 2: IO Bounded Worker

To test `--prefetch` and `--prefetch-size`

[io_bound](io_bound/app.py)