from typing import Protocol, Dict, Any
from core.entities.letter import UserTier

class AIServiceInterface(Protocol):
    def generate_content(
        self,
        prompt: str,
        user_tier: UserTier,
        max_tokens: int,
        temperature: float
    ) -> str:
        ...
