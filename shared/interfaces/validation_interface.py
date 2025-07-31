from typing import Protocol
from core.entities.letter import GenerationRequest

class ValidationServiceInterface(Protocol):
    """Interface pour le service de validation."""
    def validate_generation_request(self, request: GenerationRequest) -> None:
        """
        Valide une requête de génération.
        
        Raises:
            ValidationError: Si la requête est invalide.
        """
        ...