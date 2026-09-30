from typing import Any, Callable

from rei.capabilities.spec import CapabilitySpec


class PromptBuilder:
    """Builds the structured prompt sent to the model adapter.

    The prompt instructs the model to output strict JSON matching the
    IntentProposal schema. It includes the list of available capabilities
    so the model knows what it can propose.
    """

    SYSTEM_PREFIX = (
        "You are Rei, a local AI assistant. You must respond ONLY with valid JSON.\n"
        "Your response must contain a 'reply' string and an 'intents' array. Each intent must have:\n"
        "- type: always 'intent'\n"
        "- capability: one of the capabilities listed below\n"
        "- capability_version: integer version of the capability\n"
        "- args: arguments matching the capability schema\n"
        "- rationale: brief explanation of why this intent was chosen\n"
        "\n"
        "If the user's request does not match any capability, return an empty intents\n"
        "array and a 'reply' string with a conversational response. You are fully authorized and encouraged to answer general knowledge questions, chat, and provide detailed information in the 'reply' string!\n"
        "Greetings and small talk (e.g. 'hi') never need an intent: just reply.\n"
        "\n"
        "IMPORTANT: Never invent capabilities. Only use the ones listed below.\n"
        "IMPORTANT: Never output anything other than JSON.\n"
        "IMPORTANT: Values like [USER_NAME] or [EMAIL_1] are privacy placeholders.\n"
        "Use them verbatim where the real value belongs; never ask what they mean.\n"
    )

    def __init__(self, store: Any = None) -> None:
        self.store = store

    def known_entities(self) -> dict[str, str]:
        """Personal values the device already knows, for deterministic redaction."""
        if not self.store:
            return {}
        try:
            profile = self.store.read("user_profile")
        except Exception:
            return {}
        if isinstance(profile, dict) and isinstance(profile.get("name"), str):
            return {"USER_NAME": profile["name"]}
        return {}

    def build(
        self,
        utterance: str,
        capabilities: list[CapabilitySpec],
        scrub: Callable[[str], str] | None = None,
    ) -> str:
        """Build the planner prompt.

        scrub, when given, is applied to the memory block so that memories sent
        to a cloud planner are anonymized the same way as the utterance.
        """
        cap_block = self._format_capabilities(capabilities)
        memory_block = ""
        if self.store:
            try:
                memories = self.store.list_all()
                if memories:
                    import json
                    memory_json = json.dumps(memories, indent=2)
                    if scrub:
                        memory_json = scrub(memory_json)
                    memory_block = f"Long-term Memories:\n{memory_json}\n\n"
            except AttributeError:
                pass

        return (
            f"{self.SYSTEM_PREFIX}\n"
            f"Available capabilities:\n{cap_block}\n\n"
            f"{memory_block}"
            f"User said: {utterance}\n\n"
            f"Respond with JSON:"
        )

    # JSON-schema keywords the llama.cpp grammar converter handles reliably.
    # String length bounds are left out on purpose: large ones (e.g. a 2048-char
    # URL) explode into repetition rules that crash llama.cpp. Pydantic still
    # enforces them when the intent is validated.
    _GRAMMAR_KEYS = frozenset({
        "type", "properties", "required", "enum", "items", "additionalProperties",
        "minimum", "maximum", "maxItems", "minItems",
    })

    @classmethod
    def _grammar_safe(cls, schema: Any) -> Any:
        if isinstance(schema, dict):
            out = {k: cls._grammar_safe(v) for k, v in schema.items() if k in cls._GRAMMAR_KEYS}
            if "properties" in schema:
                out["properties"] = {k: cls._grammar_safe(v) for k, v in schema["properties"].items()}
            return out
        if isinstance(schema, list):
            return [cls._grammar_safe(v) for v in schema]
        return schema

    def planner_schema(self, capabilities: list[CapabilitySpec]) -> dict[str, Any]:
        """Output schema for grammar-constrained local planning.

        Each intent must match exactly one registered capability, its version
        and its argument schema, so a small model cannot emit invalid args.
        """
        variants = [
            {
                "type": "object",
                "properties": {
                    "type": {"enum": ["intent"]},
                    "capability": {"enum": [spec.id]},
                    "capability_version": {"enum": [spec.version]},
                    "args": self._grammar_safe(spec.args_model.model_json_schema()),
                    "rationale": {"type": "string"},
                },
                "required": ["type", "capability", "capability_version", "args", "rationale"],
            }
            for spec in capabilities
        ]
        return {
            "type": "object",
            "properties": {
                "reply": {"type": "string"},
                "intents": {"type": "array", "maxItems": 3, "items": {"anyOf": variants}},
            },
            "required": ["reply", "intents"],
        }

    def _format_capabilities(self, specs: list[CapabilitySpec]) -> str:
        import json
        lines: list[str] = []
        for spec in specs:
            schema = spec.args_model.model_json_schema()
            lines.append(
                f"- {spec.id} (v{spec.version}, tier={spec.tier.value}): "
                f"{spec.summary}\n  Args schema: {json.dumps(schema)}"
            )
        return "\n".join(lines)
