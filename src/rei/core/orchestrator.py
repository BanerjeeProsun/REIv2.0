import asyncio
import re
from typing import Any
from dataclasses import dataclass

from rei.intents.schemas import IntentProposal
from rei.intents.parser import IntentParser, IntentParserError
from rei.policy.schemas import PolicyDecision, Verdict
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.grant import GrantToken
from rei.core.cancellation import CancelToken
from rei.core.prompt_builder import PromptBuilder
from rei.models.adapter import ModelAdapter
from rei.models.router import ModelRouter, Route
from rei.models.formatter import FormatterError
from rei.egress.anonymizer import Anonymizer, Vault
from rei.capabilities.registry import CapabilityRegistry
from rei.content.guard import ContentGuard
from rei.content.envelope import TaintType
from rei.confirm.broker import ConfirmationBroker
from rei.core.executor import Executor
from rei.audit.writer import AuditLogWriter


class PipelineError(Exception):
    pass



@dataclass
class TurnResult:
    success: bool
    reply: str
    intents: list[IntentProposal]
    decisions: list[PolicyDecision]
    execution_results: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]


class Orchestrator:
    """Wired 8-stage pipeline (ARC-01, ARC-02).

    Every user request flows through exactly these stages.
    Any failure routes to the DENY branch with zero side effects.
    """

    def __init__(
        self,
        model: ModelAdapter,
        registry: CapabilityRegistry,
        policy_engine: PolicyEngine,
        parser: IntentParser,
        prompt_builder: PromptBuilder,
        confirmation_broker: ConfirmationBroker,
        executor: Executor,
        audit: AuditLogWriter | None = None,
    ) -> None:
        self.model = model
        self.registry = registry
        self.policy_engine = policy_engine
        self.parser = parser
        self.prompt_builder = prompt_builder
        self.confirmation_broker = confirmation_broker
        self.executor = executor
        self.audit = audit

    async def process_turn(
        self,
        raw_input: str,
        ctx: PolicyContext,
        cancel_token: CancelToken,
        allow_actions: bool = True,
    ) -> TurnResult:
        """Run one turn. allow_actions=False makes it purely conversational
        (e.g. the setup greeting): no capabilities are offered to the model and
        any intents it still proposes are discarded."""
        audit_events: list[dict[str, Any]] = []
        try:
            # 1. Capture
            utterance = self._capture(raw_input)
            audit_events.append({"stage": "capture", "utterance": utterance})

            # 2. Propose
            cancel_token.raise_if_cancelled()
            specs = self.registry.get_all_specs() if allow_actions else []
            shortcut = self._shortcut(utterance) if allow_actions else None
            if shortcut is not None:
                # Unambiguous commands ("pause", "next song") skip the model:
                # instant, and a small model can't misread them. Policy still applies.
                raw_output, vault = shortcut, None
                audit_events.append({"stage": "propose", "shortcut": True})
            else:
                raw_output, vault = await self._propose(utterance, ctx, cancel_token, audit_events, specs)
                audit_events.append({"stage": "propose", "output_len": len(raw_output)})

            # 3. Parse
            intents = self._parse(raw_output) if allow_actions else []
            if shortcut is None and self._planned_by_small_model(vault):
                grounded = self._ground_intents(intents, utterance)
                if len(grounded) != len(intents):
                    audit_events.append({
                        "stage": "ground",
                        "dropped": [i.capability for i in intents if i not in grounded],
                    })
                intents = grounded
            if vault is not None and len(vault):
                # Placeholders from the cloud planner are restored on-device only
                intents = [
                    i.model_copy(update={
                        "args": vault.rehydrate_obj(i.args),
                        "rationale": vault.rehydrate(i.rationale),
                    })
                    for i in intents
                ]
            audit_events.append({
                "stage": "parse",
                "intent_count": len(intents),
                "capabilities": [i.capability for i in intents],
            })

            if not intents:
                # Model returned conversational reply, no actions
                reply = self._extract_reply(raw_output)
                if vault is not None:
                    reply = vault.rehydrate(reply)
                self._write_audit(audit_events)
                return TurnResult(
                    success=True,
                    reply=reply,
                    intents=[],
                    decisions=[],
                    execution_results=[],
                    audit_events=audit_events,
                )

            decisions: list[PolicyDecision] = []
            execution_results: list[dict[str, Any]] = []
            # One outcome per intent, so the report can never pair an intent
            # with another intent's result (e.g. after a declined confirmation)
            outcomes: list[tuple[IntentProposal, str, dict[str, Any] | None]] = []

            for intent in intents:
                cancel_token.raise_if_cancelled()
                intent = self._normalise_args(intent)

                # 4. Decide
                decision = self._decide(intent, ctx)
                decisions.append(decision)
                audit_events.append({
                    "stage": "decide",
                    "capability": intent.capability,
                    "verdict": decision.verdict.name,
                    "reasons": decision.reasons,
                })

                if decision.verdict == Verdict.DENY:
                    outcomes.append((intent, "denied", {"reasons": decision.reasons}))
                    continue

                # 5. Confirm
                if decision.verdict == Verdict.CONFIRM:
                    approved = await self._confirm(intent, decision, cancel_token)
                    audit_events.append({
                        "stage": "confirm",
                        "capability": intent.capability,
                        "approved": approved,
                    })
                    if not approved:
                        outcomes.append((intent, "declined", None))
                        continue

                # 6. Grant
                grant, mac = self._grant(intent, ctx, decision)
                audit_events.append({
                    "stage": "grant",
                    "grant_id": grant.grant_id,
                    "capability": intent.capability,
                })

                # 7. Execute (off the UI thread; a failing handler fails only its intent)
                result = await self._execute(intent, grant, mac)
                execution_results.append(result)
                outcomes.append((intent, "executed", result))
                audit_events.append({
                    "stage": "execute",
                    "capability": intent.capability,
                    "status": result.get("status", "unknown"),
                })
                # Content read from outside (e.g. an email) taints the rest of the turn
                taint = result.get("taint")
                if isinstance(taint, str) and taint in TaintType.__members__:
                    ctx = ContentGuard().propagate_taint(ctx, [TaintType(taint)])

            # 8. Report. Per executed intent, in order of preference:
            #  - its own "spoken" line (deterministic, e.g. "Playing X.", an inbox summary)
            #  - a tool-free model summary of returned "content" (untrusted, fenced)
            #  - the generic "Done: ..." report
            parts: list[str] = []
            to_summarize: list[tuple[IntentProposal, dict[str, Any]]] = []
            rest: list[tuple[IntentProposal, str, dict[str, Any] | None]] = []
            for intent, status, r in outcomes:
                if status == "executed" and r is not None and r.get("status") == "success" \
                        and isinstance(r.get("spoken"), str):
                    parts.append(str(r["spoken"]))
                elif status == "executed" and r is not None and isinstance(r.get("content"), str):
                    to_summarize.append((intent, r))
                else:
                    rest.append((intent, status, r))
            if to_summarize:
                parts.append(await self._summarize_results(utterance, to_summarize, cancel_token))
                audit_events.append({"stage": "summarize", "sources": [i.capability for i, _ in to_summarize]})
            if rest:
                parts.append(self._report(rest))
            reply = " ".join(p for p in parts if p) or "No actions were taken."
            if vault is not None:
                reply = vault.rehydrate(reply)
            self._write_audit(audit_events)

            return TurnResult(
                success=True,
                reply=reply,
                intents=intents,
                decisions=decisions,
                execution_results=execution_results,
                audit_events=audit_events,
            )

        except (Exception, asyncio.CancelledError) as e:
            audit_events.append({"stage": "deny", "error": str(e)})
            self._write_audit(audit_events)
            return TurnResult(
                success=False,
                reply=f"I was unable to complete that request. Reason: {e}",
                intents=[],
                decisions=[],
                execution_results=[],
                audit_events=audit_events,
            )

    # Stage implementations

    def _capture(self, raw_input: str) -> str:
        return raw_input.strip()

    def _write_audit(self, audit_events: list[dict[str, Any]]) -> None:
        if self.audit:
            for event in audit_events:
                self.audit.write_event(event.get("stage", "unknown"), event)

    async def _propose(
        self,
        utterance: str,
        ctx: PolicyContext,
        cancel_token: CancelToken,
        audit_events: list[dict[str, Any]],
        specs: list[Any],
    ) -> tuple[str, Vault | None]:
        """Local Formatter -> Cloud Planner.

        Local route: the raw utterance never leaves the device.
        Cloud route: deterministic scrub + local span detection first; the
        placeholder vault stays on-device so the reply can be rehydrated.
        If the formatter fails, fail closed and plan locally.
        """
        router = self.model if isinstance(self.model, ModelRouter) else None

        if router is None:
            prompt = self.prompt_builder.build(utterance, specs)
            return await self.model.generate(prompt, cancel_token), None

        local_router: ModelRouter = router

        async def plan_locally() -> tuple[str, Vault | None]:
            # The local model may see the raw utterance; nothing leaves the device
            prompt = self.prompt_builder.build(utterance, specs)
            schema = self.prompt_builder.planner_schema(specs)
            return await local_router.generate_local(prompt, cancel_token, schema=schema), None

        if router.route(ctx.privacy_mode) is Route.LOCAL:
            return await plan_locally()

        vault = Vault()
        anonymizer = Anonymizer(self.prompt_builder.known_entities())
        sanitized = anonymizer.scrub(utterance, vault)
        formatter_status = "unavailable"
        if router.formatter is not None:
            try:
                spans = await router.formatter.detect_spans(sanitized, cancel_token)
                sanitized = anonymizer.apply_spans(sanitized, spans, vault)
                formatter_status = "ok"
            except FormatterError as e:
                print(f"[Orchestrator] {e}. Failing closed: planning locally.")
                audit_events.append({"stage": "sanitize", "route": "local", "formatter": "failed"})
                return await plan_locally()

        prompt = self.prompt_builder.build(
            sanitized, specs, scrub=lambda text: anonymizer.scrub(text, vault)
        )
        # Counts only; never the values or the mapping
        audit_events.append({
            "stage": "sanitize",
            "route": "cloud",
            "formatter": formatter_status,
            "placeholders": len(vault),
            "secrets_removed": anonymizer.stats.secrets_removed,
            "spans_replaced": anonymizer.stats.spans_replaced,
        })

        try:
            return await router.generate_cloud(prompt, cancel_token), vault
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if router.local_model is None:
                raise
            print(f"Cloud Model failed ({e}). Falling back to Local Model...")
            return await plan_locally()

    # Words too generic to show the user asked for a specific capability
    # ("type"/"writing" stay meaningful: they're how people ask to type text)
    _GROUNDING_STOPWORDS = frozenset({
        "the", "and", "for", "set", "using", "useful", "piece", "information",
        "long", "term", "system", "apps", "application", "media", "web",
        "messages", "documents", "text", "keyboard", "browser",
    })

    def _planned_by_small_model(self, vault: Vault | None) -> bool:
        """True when this turn's plan came from the on-device router model."""
        return (
            isinstance(self.model, ModelRouter)
            and vault is None
            and self.model.local_model is not None
        )

    def _grounding_score(self, intent: IntentProposal, utterance: str) -> tuple[bool, int]:
        """How strongly the user's words point at this intent.

        Grammar-constrained 1B output is always well formed, so without this
        "hi" can come back as system.lock. An intent is grounded when a
        capability keyword (e.g. "lock", "volume") or a fixed-choice action
        ("pause", "restart") appears in the utterance. Free-text args never
        count: they can simply echo the utterance.
        """
        words = re.findall(r"[a-z0-9]+", utterance.lower())
        try:
            spec = self.registry.get_spec(intent.capability)
        except Exception:
            return False, 0
        keywords = {
            k for k in re.findall(r"[a-z]+", f"{intent.capability} {spec.summary}".lower().replace("_", " "))
            if len(k) >= 3 and k not in self._GROUNDING_STOPWORDS
        }
        keyword_hits = sum(
            1 for k in keywords if any(w.startswith(k[:4]) for w in words if len(w) >= 3)
        )
        action_hit = False
        enum_hits = 0
        properties = spec.args_model.model_json_schema().get("properties", {})
        for key, value in intent.args.items():
            if properties.get(key, {}).get("enum") and isinstance(value, str) and value.lower() in words:
                enum_hits += 1
                action_hit = action_hit or key == "action"
        # Free-text args that echo the user's words (e.g. music.play's query
        # "lofi hip hop") mark the more specific capability: a scoring bonus only,
        # never a reason to keep an intent on its own.
        echo = 0
        for key, value in intent.args.items():
            if isinstance(value, str) and not properties.get(key, {}).get("enum"):
                echo += sum(1 for w in set(re.findall(r"[a-z0-9]+", value.lower())) if len(w) >= 3 and w in words)
        return keyword_hits > 0 or action_hit, keyword_hits + enum_hits + min(echo, 3)

    def _ground_intents(self, intents: list[IntentProposal], utterance: str) -> list[IntentProposal]:
        scored = [(i, *self._grounding_score(i, utterance)) for i in intents]
        grounded = [(i, score) for i, ok, score in scored if ok]
        multi_step = re.search(r"\b(and|then|also|after that)\b|[,;]", utterance.lower())
        if len(grounded) > 1 and not multi_step:
            # One request, one action: keep the best-supported intent
            grounded = [max(grounded, key=lambda pair: pair[1])]
        return [i for i, _ in grounded]

    _MEDIA_SHORTCUT = re.compile(
        r"^(?:(?:please|can you|could you)\s+)?"
        r"(pause|stop|resume|continue|unpause|play|next|skip|previous|go back)"
        r"(?:\s+(?:the|this|that|my))?(?:\s+(?:music|song|track|playback|it|audio))?"
        r"(?:\s+please)?[\s.!?]*$",
        re.IGNORECASE,
    )
    _MEDIA_ACTIONS = {"pause": "pause", "stop": "stop", "resume": "play", "continue": "play",
                      "unpause": "play", "play": "play", "next": "next", "skip": "next",
                      "previous": "prev", "go back": "prev"}

    def _shortcut(self, utterance: str) -> str | None:
        """Plan for commands too simple to need a model, e.g. "pause the music",
        "next song", "stop". Returns planner-style JSON, or None."""
        match = self._MEDIA_SHORTCUT.match(utterance.strip())
        if not match:
            return None
        try:
            spec = self.registry.get_spec("media.control")
        except Exception:
            return None
        import json
        action = self._MEDIA_ACTIONS[match.group(1).lower()]
        return json.dumps({"reply": "", "intents": [{
            "type": "intent", "capability": spec.id, "capability_version": spec.version,
            "args": {"action": action}, "rationale": "media shortcut",
        }]})

    def _parse(self, raw_output: str) -> list[IntentProposal]:
        try:
            intents = self.parser.parse(raw_output)
        except IntentParserError:
            return []
        # Small models often repeat the same intent; run each action once
        unique: list[IntentProposal] = []
        for intent in intents:
            if intent not in unique:
                unique.append(intent)
        return unique

    def _decide(self, intent: IntentProposal, ctx: PolicyContext) -> PolicyDecision:
        return self.policy_engine.decide(intent, ctx)

    async def _confirm(
        self,
        intent: IntentProposal,
        decision: PolicyDecision,
        cancel_token: CancelToken,
    ) -> bool:
        cancel_token.raise_if_cancelled()
        return await self.confirmation_broker.request_confirmation(intent, decision)

    def _grant(
        self,
        intent: IntentProposal,
        ctx: PolicyContext,
        decision: PolicyDecision,
    ) -> tuple[GrantToken, str]:
        return self.policy_engine.issue_grant(intent, ctx, decision)

    async def _execute(
        self,
        intent: IntentProposal,
        grant: GrantToken,
        mac: str,
    ) -> dict[str, Any]:
        args_model = self.registry.get_spec(intent.capability).args_model
        validated_args = args_model.model_validate(intent.args)
        try:
            # Handlers may block (typing, network, launching apps): keep the UI responsive
            result: dict[str, Any] = await asyncio.to_thread(self.executor.execute, grant, validated_args, mac)
        except Exception as e:
            print(f"[Orchestrator] {intent.capability} failed: {e}")
            error = str(e).removeprefix("Capability execution failed: ")
            return {"status": "error", "error": error}
        # The executor wraps the handler's return value as {"status", "data"}.
        # Lift the handler's fields (spoken, content, taint...) so they are seen.
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict):
            return {**data, "status": data.get("status", result.get("status", "success"))}
        return result

    def _normalise_args(self, intent: IntentProposal) -> IntentProposal:
        """Fill in defaults so the grant hashes exactly what the executor will
        run (a model often omits optional args; the executor validates them
        into the full set, which used to fail grant verification)."""
        try:
            spec = self.registry.get_spec(intent.capability)
            full = spec.args_model.model_validate(intent.args).model_dump(mode="json")
        except Exception:
            return intent  # invalid args: let the policy engine reject them
        return intent.model_copy(update={"args": full})

    def _describe(self, intent: IntentProposal) -> str:
        """Human phrase for an intent, from its own confirm template (not the
        model's rationale, which small models often get wrong)."""
        try:
            spec = self.registry.get_spec(intent.capability)
            return spec.confirm_template.format(**intent.args)
        except Exception:
            return intent.capability

    def _report(
        self,
        outcomes: list[tuple[IntentProposal, str, dict[str, Any] | None]],
    ) -> str:
        parts: list[str] = []
        for intent, status, result in outcomes:
            what = self._describe(intent).rstrip(" .!?")
            if status == "denied":
                reasons = ", ".join((result or {}).get("reasons", [])) or "policy"
                parts.append(f"I'm not allowed to do that ({what}): {reasons}.")
            elif status == "declined":
                parts.append(f"Okay, cancelled: {what}.")
            elif result and result.get("status") == "success":
                parts.append(f"Done: {what}.")
            else:
                error = (result or {}).get("error", "unknown error")
                parts.append(f"That didn't work ({what}): {error}.")
        return " ".join(parts) if parts else "No actions were taken."

    RESULTS_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {"reply": {"type": "string"}},
        "required": ["reply"],
    }

    async def _summarize_results(
        self,
        utterance: str,
        results: list[tuple[IntentProposal, dict[str, Any]]],
        cancel_token: CancelToken,
    ) -> str:
        """Answer the user from capability results (e.g. emails that were read).

        The results are untrusted: they are sanitised and fenced in
        UNTRUSTED_CONTENT envelopes, and this call offers NO capabilities, so
        instructions hidden in the content can never trigger an action. It runs
        on the local model, so the content never leaves the device.
        """
        guard = ContentGuard()
        blocks = []
        for intent, result in results:
            taint = result.get("taint")
            if not (isinstance(taint, str) and taint in TaintType.__members__):
                taint = "DOCUMENT"
            envelope = guard.encapsulate(str(result["content"])[:6000], intent.capability, TaintType(taint))
            blocks.append(envelope.format_for_model())
        prompt = self.prompt_builder.build_results_prompt(utterance, blocks)

        router = self.model if isinstance(self.model, ModelRouter) else None
        try:
            if router is not None and router.local_model is not None:
                raw = await router.generate_local(prompt, cancel_token, schema=self.RESULTS_SCHEMA)
            else:
                raw = await self.model.generate(prompt, cancel_token)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[Orchestrator] results summary failed: {e}")
            return "I got the results but couldn't summarise them."
        return self._extract_reply(raw)

    FALLBACK_REPLY = "I'm not sure how to help with that."
    REPLY_KEYS = ("reply", "response", "message", "text", "answer")

    def _extract_reply(self, raw_output: str) -> str:
        """Pull the conversational reply out of whatever the model produced.

        Accepts strict JSON, JSON wrapped in prose or code fences, alternate
        reply keys, and plain conversational text (common from small models).
        """
        text = raw_output.strip()
        if not text:
            return self.FALLBACK_REPLY

        data = self._first_json_value(text)
        if data is None:
            # No JSON at all: the model just chatted. Use it as the reply.
            return text.strip("`").strip() or self.FALLBACK_REPLY

        if isinstance(data, dict):
            for key in self.REPLY_KEYS:
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return self.FALLBACK_REPLY

    @staticmethod
    def _first_json_value(text: str) -> Any:
        import json
        decoder = json.JSONDecoder()
        for i, ch in enumerate(text):
            if ch in "{[":
                try:
                    value, _ = decoder.raw_decode(text, i)
                    return value
                except json.JSONDecodeError:
                    continue
        return None
