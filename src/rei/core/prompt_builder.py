from rei.capabilities.spec import CapabilitySpec


class PromptBuilder:
    """Builds the structured prompt sent to the model adapter.
    
    The prompt instructs the model to output strict JSON matching the
    IntentProposal schema. It includes the list of available capabilities
    so the model knows what it can propose.
    """

    SYSTEM_PREFIX = (
        "You are Rei, a local AI assistant. You must respond ONLY with valid JSON.\n"
        "Your response must contain an 'intents' array. Each intent must have:\n"
        "- type: always 'intent'\n"
        "- capability: one of the capabilities listed below\n"
        "- capability_version: integer version of the capability\n"
        "- args: arguments matching the capability schema\n"
        "- rationale: brief explanation of why this intent was chosen\n"
        "\n"
        "If the user's request does not match any capability, return an empty intents\n"
        "array and a 'reply' string with a conversational response.\n"
        "\n"
        "IMPORTANT: Never invent capabilities. Only use the ones listed below.\n"
        "IMPORTANT: Never output anything other than JSON.\n"
    )

    def __init__(self, store=None):
        self.store = store

    def build(
        self,
        utterance: str,
        capabilities: list[CapabilitySpec],
    ) -> str:
        cap_block = self._format_capabilities(capabilities)
        memory_block = ""
        if self.store:
            memories = self.store.get_all()
            if memories:
                import json
                memory_block = f"Long-term Memories:\n{json.dumps(memories, indent=2)}\n\n"
        
        return (
            f"{self.SYSTEM_PREFIX}\n"
            f"Available capabilities:\n{cap_block}\n\n"
            f"{memory_block}"
            f"User said: {utterance}\n\n"
            f"Respond with JSON:"
        )

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
