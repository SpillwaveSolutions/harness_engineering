# Chapter 10 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Sandbox and credential-isolation listings for the travel-booking agent.
Every listing imports with no API keys and no network. Live Modal calls
run only when `MODAL_TOKEN_ID` is set.

| File | What it does |
| --- | --- |
| `listings/10-02-worktree-lifecycle.py` | Creates a git worktree, calls `invoke_agent`, and gates on pytest. |
| `listings/10-03-sandbox-as-tool.py` | `build_sandbox_agent()` returns an offline sandbox agent unless Modal credentials are present. |
| `listings/10-04-credential-isolation.py` | `CredentialProxy` checks the host allowlist and redacts the vault token. |
| `listings/10-06-sandbox-abstraction.py` | `ExecutionResult` plus the `SandboxBackend` protocol. |

## Setup

```bash
cd code/chapter10
uv sync --all-groups
```

## Run offline

```bash
uv run python listings/10-02-worktree-lifecycle.py
uv run python listings/10-03-sandbox-as-tool.py
uv run python listings/10-04-credential-isolation.py
uv run python listings/10-06-sandbox-abstraction.py
```

Expected offline output:

```text
{"status": "ok", "task": "book a flight"}
{"status": "offline"}
Invalid session token
stdout='' stderr='' returncode=0
```

`10-03` also prints `MODAL_TOKEN_ID is unset; sandbox agent is offline.`
on stderr. `10-02`'s demo calls `invoke_agent` only. It does not create
a git worktree.

## Tests

```bash
uv run pytest -q
```

Tests call the listing functions and assert the offline results.

## Live calls

Set `HARNESS_LIVE_API=1` together with `MODAL_TOKEN_ID` and
`MODAL_TOKEN_SECRET` before calling `build_sandbox_agent()` if you want
the Modal lookup. The default test run does not do that.
