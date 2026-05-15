# Evaluation

The full evaluation lives in [`evaluation/`](evaluation/).

- **Rendered report:** [`evaluation/report.html`](evaluation/report.html) — open in any browser
- **Methodology, results, caveats:** [`evaluation/README.md`](evaluation/README.md)
- **Pre-registration:** [`evaluation/preregistration-sonnet.md`](evaluation/preregistration-sonnet.md) (committed before Sonnet data existed)
- **Raw data:** [`evaluation/raw-opus/`](evaluation/raw-opus/), [`evaluation/raw-sonnet/`](evaluation/raw-sonnet/) — stream-json from all 60 measurement runs
- **Scripts:** [`evaluation/scripts/`](evaluation/scripts/) — strip script, harness, parser, report builder

## Headline (N=10 per cell across both models)

Median input tokens to first edit:

| Model | Arm A (stripped) | Arm B (skill) | Arm C (human) | Δ B vs A | Δ C vs A |
|---|---|---|---|---|---|
| **Opus 4.7** | 405,939 | 403,236 | 438,718 | **−0.7%** | **+8.1%** |
| **Sonnet 4.6** | 557,902 | 700,377 | 445,117 | **+25.5%** | **−20.2%** |

On Opus, doc comments have approximately no effect on agent cost. On Sonnet, doc-comment *quality* matters: human-written docs reduce cost by 20%; the skill's generated docs increase cost by 25%. The skill is never better than human docs across the tested capability range.

See [`evaluation/README.md`](evaluation/README.md) for the full design, mechanism analysis, and honest caveats.
