from abc import ABC, abstractmethod
from rei.core.cancellation import CancelToken


class ModelAdapter(ABC):
    """Abstract interface for all model backends (MOD-01).
    
    Every model call in Rei goes through this interface.
    Models influence proposals but never decide actions.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        cancel_token: CancelToken,
        deadline_ms: int = 5000,
    ) -> str:
        """Generate a completion from the given prompt.
        
        Args:
            prompt: The full system + user prompt.
            cancel_token: Checked before and during generation.
            deadline_ms: Hard deadline for the generation call.
            
        Returns:
            Raw model output string (to be parsed by IntentParser).
            
        Raises:
            asyncio.CancelledError: If cancel_token fires.
            TimeoutError: If deadline_ms is exceeded.
        """
        ...
