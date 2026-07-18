# Self-Improvement Change Budget Model

Task: AION-165

## Budget Dimensions

Every proposal must declare maximum files, maximum insertions, maximum deletions, maximum dependency changes, maximum protected paths, maximum benchmark cost, and maximum canary exposure.

## Default Budget Table

| Risk | Max files | Max insertions | Max deletions | Max dependency changes | Max protected paths | Max benchmark cost units | Max canary exposure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 5 | 250 | 120 | 0 | 0 | 10 | 0 |
| medium | 12 | 800 | 300 | 0 | 0 | 25 | 0 |
| high | 20 | 1500 | 600 | 0 | 0 | 50 | 0 |
| critical | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Critical proposals are blocked from ordinary self-improvement execution and require separate governance authorization.

## Enforcement

Budget overruns block approval. Safety failures cannot be offset by quality score, benchmark gain, or operator convenience.
