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

## Development Progress

### Completed Milestones
The foundational architecture and core security boundaries have been established:
* Canonical Runtime and Pipeline: A strict 8-stage execution pipeline is in place.
* Process Supervisor: Job Object backed process supervision with crash loop protection and graceful shutdown handles.
* Capability Registry: Legacy shell execution has been completely replaced by a typed capability registry (e.g., apps.open, media.set_volume, web.open_url) using strict Pydantic schemas.
* Policy Engine: A pure, deterministic policy engine evaluates intents based on integrity, kill switches, origin, taint, and data classification.
* Grant Verification: Cryptographically verified GrantTokens enforce that execution only occurs with explicit engine approval.
* Development Tooling: Strict mypy typing, ruff linting, and importlinter zone boundaries are fully configured and passing in CI.

### Coming Soon
* Privacy Modes and Egress Gate: Implementation of the socket guard and egress broker to enforce local_only zero-egress guarantees.
* Content Guard and Taint Propagation: Sandboxing untrusted inputs (email, web, clipboard) inside envelopes and propagating taint across the execution pipeline.
* Confirmation Broker: Interactive UI cards for risk-tier capabilities requiring explicit user approval.
* Interim API Hardening: Per-launch token authentication and origin validation for local API endpoints.
* Phase P1 (Consolidation): Named-pipe IPC, encrypted SQLite memory storage, and hash-pinned dependency management.
* Phase P2 (Engineering Quality): Quarantined reader mode for untrusted content and constrained decoding for models.
* Phase P3 (Advanced Hardening): Separated host processes, Windows Firewall rules, and Authenticode signing.

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
