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

### Phase P0 and P1 Completed
The foundational architecture, security boundaries, and local containment infrastructure have been fully implemented and verified:
* Canonical Runtime and Pipeline: A strict 8-stage execution pipeline is in place.
* Process Supervisor: Job Object backed process supervision with crash loop protection.
* Capability Registry: Legacy shell execution has been completely replaced by a typed capability registry using strict Pydantic schemas.
* Policy Engine: A pure, deterministic policy engine evaluates intents based on integrity, kill switches, origin, taint, and data classification.
* Cryptographic Grants: Verified GrantTokens enforce that execution only occurs with explicit engine approval.
* Privacy Modes and Egress Gate: Implementation of the socket guard, redactor, and egress broker to enforce zero-egress guarantees in local mode.
* Content Guard and Taint Propagation: Untrusted inputs are sandboxed inside envelopes, propagating taint across the execution pipeline to block prompt injections.
* Confirmation Broker: Interactive UI card routing for high-risk capabilities requiring explicit user approval.
* Named-Pipe IPC: High-security inter-process communication using Windows Named Pipes, restricted by user SID and client PID, fully replacing vulnerable HTTP localhost endpoints.
* Memory and Configuration: Data is stored in SQLite encrypted at rest via Windows DPAPI. Secrets are stored strictly in the Windows Credential Manager.
* Observability: Cryptographically chained audit logs with recursive PII and secret redaction.
* CI Gates: Reproducible builds locked via uv.lock and models.lock, strict typing, import boundaries, and comprehensive unit tests.

### Coming Soon
* Phase P2 (Engineering Quality and UX): Implementation of a Quarantined Reader mode for summarizing untrusted content without side effects, constrained decoding optimizations for models, and performance tuning for the Voice Activity Detection (VAD) and local Text-to-Speech (TTS) pipelines.
* Phase P3 (Advanced Hardening): Process separation for the capability host, Windows Firewall rules per mode, external penetration testing, and Authenticode signing.

## Development

Prerequisites:
* Python 3.11 or higher
* uv (Python package manager)

Setup the repository:
```cmd
uv sync --all-extras
```

Run tests and linters:
```cmd
uv run ruff check src tests
uv run mypy src tests
uv run lint-imports
uv run pytest tests
```

## Documentation

Authoritative architecture details, delivery phases, and the threat model are defined in the Architecture Bible located in the docs directory.
