# news1118-entry

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/RizqiSeijuuro/news1118-entry/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/RizqiSeijuuro/news1118-entry/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

A standard-library-only Python 3.13 program that hand-encodes a PNG (via `zlib` + `struct`, with a custom 5x7 bitmap font) to render a 1024x1024 "World News" dashboard summarizing six major stories from 18 November 2026 — the Russian strikes on Odesa's historic centre, the EU's proposed 45 billion euro loan for Ukraine, UNICEF's report on children killed in Yemen's conflict, the WHO's warning on worsening antibiotic resistance, a wave of US tech outages across air travel, Microsoft email, and the NSA, and the alleged Iranian plot targeting Washington DC. No network access or third-party libraries are used at runtime, and the output is byte-for-byte deterministic across runs.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
