# Contributing

## Setup

```bash
git clone https://github.com/Hemakrishna7406/agent-studio-woocommerce-connector.git
cd agent-studio-woocommerce-connector
make dev          # install dev dependencies
make demo         # run the zero-setup offline demo
make test         # run the test suite
```

## Before you open a PR

```bash
make lint         # ruff
make typecheck    # mypy
make test         # pytest
```

All three must pass. CI runs the same checks on Python 3.11 and 3.12.

## Ground rules

- **Never commit secrets.** `.env` is gitignored; use `.env.example` for
  placeholders. Tests must not hit the network — use the `FakeSession` in
  `tests/conftest.py`.
- **Keep the core framework-agnostic.** `connector/` must not import `mcp`.
  MCP stays a thin adapter in `mcp_server/`.
- **New tool? Document it.** Add it to `docs/mcp-tool-spec.md` and update
  `docs/capabilities.md`.
- **Keep it read-only** unless the change is explicitly about writes, in which
  case it must ship with human-in-the-loop approval and an audit trail.

## Commit style

Conventional-ish: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
