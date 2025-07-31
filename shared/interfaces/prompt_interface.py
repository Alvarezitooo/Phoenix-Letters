from typing import Protocol
from core.entities.letter import GenerationRequest

class PromptServiceInterface(Protocol):
    """Interface pour le service de construction de prompts."""
    def build_letter_prompt(self, request: GenerationRequest) -> str:
        """
        Construit le prompt pour la génération de lettre.
        """
        ...

    def build_analysis_prompt(self, letter_content: str, generation_request: GenerationRequest) -> str:
        """
        Construit le prompt pour l'analyse de lettre.
        """
        ...