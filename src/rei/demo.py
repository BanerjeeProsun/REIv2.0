"""Rei v2.0 Terminal Demo.

Run with: uv run python -m rei.demo

This demo harness proves the full 8-stage pipeline works end-to-end
using the FakeModel. Type natural language commands and watch Rei
parse intents, evaluate policy, issue grants, and execute capabilities.
"""

import asyncio
import secrets

from rei.core.orchestrator import Orchestrator
from rei.core.cancellation import CancelToken
from rei.core.prompt_builder import PromptBuilder
from rei.models.fake import FakeModel
from rei.intents.parser import IntentParser
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode
from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin import register_builtin
from rei.confirm.broker import ConfirmationBroker, UIClientMock
from rei.core.executor import Executor
from rei.host.verify import GrantVerifier


def create_orchestrator() -> Orchestrator:
    """Build a fully wired orchestrator with FakeModel."""
    grant_key = secrets.token_bytes(32)

    registry = CapabilityRegistry()
    register_builtin(registry)

    policy_config = {
        "version": "2026.09.1",
        "defaults": {"safe_mode": False},
        "disabled": {"capabilities": []},
        "preauthorise": {"allowed": ["apps.open", "media.set_volume", "web.open_url"]},
    }

    policy_engine = PolicyEngine(registry, policy_config, grant_key)
    parser = IntentParser()
    prompt_builder = PromptBuilder()
    model = FakeModel()
    broker = ConfirmationBroker(UIClientMock())
    verifier = GrantVerifier(registry, grant_key)
    executor = Executor(registry, verifier)

    return Orchestrator(
        model=model,
        registry=registry,
        policy_engine=policy_engine,
        parser=parser,
        prompt_builder=prompt_builder,
        confirmation_broker=broker,
        executor=executor,
    )


async def run_demo() -> None:
    orchestrator = create_orchestrator()

    print("=" * 60)
    print("  Rei v2.0 Terminal Demo")
    print("  Type a command. Type 'quit' to exit.")
    print("  Try: 'open notepad', 'set volume to 50', 'open google'")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        cancel_token = CancelToken()
        ctx = PolicyContext(
            session_id="demo-session",
            turn_id=f"turn-{secrets.token_hex(4)}",
            origin=Origin.USER_TYPED,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
            taint=frozenset(),
            settings={},
            recent=None,
        )

        result = await orchestrator.process_turn(user_input, ctx, cancel_token)

        print()
        if result.success:
            print(f"Rei > {result.reply}")
        else:
            print(f"Rei > [ERROR] {result.reply}")

        if result.intents:
            print(f"  Intents: {[i.capability for i in result.intents]}")
        if result.decisions:
            print(f"  Decisions: {[d.verdict.name for d in result.decisions]}")
        if result.execution_results:
            for r in result.execution_results:
                print(f"  Execution: {r.get('status', 'unknown')}")
        print()


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
