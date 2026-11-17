# Chapter 15 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Checkpoints, deterministic replay, recovery selection, and the resumable
initializer / coding-agent loop.

Importing a listing does not run git and does not call a model. A missing
`ANTHROPIC_API_KEY`, or `HARNESS_LIVE_API` other than `1`, produces one
stderr line and a deterministic offline result.

## Setup

```bash
cd code/chapter15
uv sync --all-groups
```

## Tests

```bash
uv run pytest
```

## Run

Offline coding session (no model, no git):

```bash
uv run python -c 'import json, importlib.util; from pathlib import Path; d=Path("/tmp/ch15-offline"); d.mkdir(exist_ok=True); (d/"feature_list.json").write_text(json.dumps([{"description":"Search flights","passes":False,"steps":[]}])); p="listings/15-09-coding-agent.py"; s=importlib.util.spec_from_file_location("c", p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.run_coding_session(d, 1))'
```

Expected stderr:

```
offline: HARNESS_LIVE_API is not 1 or ANTHROPIC_API_KEY is unset
```

Expected stdout:

```
{'status': 'offline', 'session': 1, 'feature': 'Search flights'}
```

Set `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` to send the initializer or
coding session to the model. Git runs only when that session is actually
executing (initializer scaffolding, or a coding session that has a client).
