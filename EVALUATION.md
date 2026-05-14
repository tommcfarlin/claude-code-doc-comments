# Evaluation

The full evaluation lives in [`evaluation/`](evaluation/).

- **Rendered report:** [`evaluation/report.html`](evaluation/report.html) — open in any browser
- **Methodology, results, caveats:** [`evaluation/README.md`](evaluation/README.md)
- **Raw data:** [`evaluation/raw/`](evaluation/raw/) — stream-json from all 15 measurement runs
- **Scripts:** [`evaluation/scripts/`](evaluation/scripts/) — strip script, harness, parser, report builder

## Headline

The skill's stated premise — that doc comments reduce the input-token cost an agent pays during discovery — was **not supported** on the tested fixture/task/model combination.

| Arm | Median input tokens to first edit | Δ vs A |
|---|---|---|
| A — stripped (no docs) | 355,942 | — |
| B — skill-generated | 408,297 | **+14.7%** |
| C — human-written | 425,455 | **+19.5%** |

15 runs, N=5 per arm, Opus 4.7, same locked prompt across all runs. See [`evaluation/README.md`](evaluation/README.md) for the full design and honest caveats.
