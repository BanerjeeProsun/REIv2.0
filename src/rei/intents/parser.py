import json
from pydantic import ValidationError
from rei.intents.schemas import IntentProposal

class IntentParserError(Exception):
    pass

class IntentParser:
    def __init__(self) -> None:
        self.max_intents_per_turn = 3

    def parse(self, raw_output: str) -> list[IntentProposal]:
        """
        Parses raw model output into a list of IntentProposals.
        Expects a JSON array of objects or a single JSON object.
        """
        try:
            # Simple extraction: find the first '[' or '{' and last ']' or '}'
            start_idx = min((raw_output.find(c) for c in "[{" if c in raw_output), default=-1)
            end_idx = max((raw_output.rfind(c) for c in "]}" if c in raw_output), default=-1)
            
            if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
                raise IntentParserError("No JSON structure found in output")
                
            json_str = raw_output[start_idx:end_idx+1]
            parsed_json = json.loads(json_str)
            
            if isinstance(parsed_json, dict):
                parsed_json = [parsed_json]
                
            if not isinstance(parsed_json, list):
                raise IntentParserError("Output must be a JSON array of intents")
                
            # Cap to max 3 intents, log excess (CAP-10)
            if len(parsed_json) > self.max_intents_per_turn:
                print(f"Warning: Model proposed {len(parsed_json)} intents, capping to {self.max_intents_per_turn}")
                parsed_json = parsed_json[:self.max_intents_per_turn]
                
            intents = []
            for item in parsed_json:
                if item.get("type") != "intent":
                    continue
                try:
                    proposal = IntentProposal.model_validate(item)
                    intents.append(proposal)
                except ValidationError as e:
                    raise IntentParserError(f"SCHEMA_INVALID: {e}")
                    
            return intents
            
        except json.JSONDecodeError as e:
            raise IntentParserError(f"Invalid JSON: {e}")
