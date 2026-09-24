# Rei
Local-first AI operating layer for Windows.

Rei is an AI assistant architecture rebuilt from the ground up to ensure strict security, user privacy, and high performance. It adheres strictly to the principle that model output is an intent, never an action. 

## Core Principles

1. Strict Security Boundaries
Model outputs are treated as untrusted data. They are parsed into typed intents, evaluated by a deterministic policy engine, and require cryptographic GrantTokens before execution. Arbitrary shell access is entirely prohibited.

2. Privacy by Default
Rei operates natively in a local-only mode. All network egress is explicitly categorized and routed through a single constrained egress broker. User content such as clipboard data, screen contents, and private documents is classified as Secret and never leaves the device.

3. Deterministic Policy
A side-effect-free policy engine evaluates all actions based on capability tiers, origin, and taint state. Untrusted external content is structurally isolated and propagated as taint, ensuring that no prompt injection can bypass the capability authorization flow.

## Architecture Structure

The repository is organized into five strict trust zones:
* Untrusted Sources: External content wrappers and sanitizers.
* UI Process: Interface rendering and audio capture.
* Rei Core: Pipeline orchestration, policy evaluation, and capability intent parsing.
* Capability Host: The isolated execution environment processing typed capability side effects.
* Egress Broker: The single, restricted network client.

## Development

Prerequisites:
* Python 3.11 or higher
* uv (Python package manager)

Setup the repository:
```cmd
uv sync
```

Run tests and linters:
```cmd
uv run ruff check src tests
uv run mypy src tests
uv run lint-imports
uv run pytest tests/unit
```

## Documentation

Authoritative architecture details, delivery phases, and the threat model are defined in the Architecture Bible located in the docs directory.
