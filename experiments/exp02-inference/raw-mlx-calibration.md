# Raw mlx-lm Calibration

This is a pre-benchmark calibration run and is not part of the controlled 2K/16K/32K comparison.

Configuration:

- prompt tokens: 512
- generation tokens: 1024
- batch size: 1
- warm-up performed by mlx_lm.benchmark

Results:

| Trial | Prompt tok/s | Generation tok/s | Peak memory GB | Total time s |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1853.359 | 95.281 | 17.755 | 11.073 |
| 2 | 1830.301 | 94.496 | 17.755 | 11.166 |
| 3 | 1821.550 | 96.596 | 17.755 | 10.933 |
| 4 | 1856.356 | 95.482 | 17.756 | 11.050 |
| 5 | 1855.341 | 95.481 | 17.756 | 11.050 |

Mean:

- prompt throughput: 1843.381 tok/s
- generation throughput: 95.467 tok/s
- peak memory: 17.755 GB
