import logging
from typing import Optional

from core.entities.letter import GenerationRequest, UserTier
from shared.interfaces.prompt_interface import PromptServiceInterface
from config.settings import Settings

logger = logging.getLogger(__name__)

class PromptService(PromptServiceInterface):
    """Service pour la construction des prompts destinés à l'IA."""

    def __init__(self, settings: Settings):
        self.settings = settings
        logger.info("PromptService initialized")

    def build_letter_prompt(self, request: GenerationRequest) -> str:
        """
        Construit le prompt pour la génération de lettre de motivation.
        """
        # Exemple de construction de prompt, à affiner selon les besoins
        prompt = f"""
        Rédige une lettre de motivation percutante pour un poste de {request.job_title} chez {request.company_name}.
        Voici le contenu de l'offre d'emploi:
        {request.job_offer_content}

        Voici le contenu du CV du candidat:
        {request.cv_content}

        Le candidat souhaite adopter un ton {request.tone.value}.
        {f"Le candidat est en reconversion et ses compétences transférables sont: {request.transferable_skills}" if request.is_career_change else ""}

        La lettre doit être concise, professionnelle et mettre en avant l'adéquation entre le profil du candidat et les exigences du poste.
        """
        return prompt.strip()

    def build_analysis_prompt(self, letter_content: str, generation_request: GenerationRequest) -> str:
        """
        Construit le prompt pour l'analyse d'une lettre de motivation.
        """
        # Exemple de construction de prompt pour l'analyse
        prompt = f"""
        Analyse la lettre de motivation suivante et attribue-lui un score sur 10.
        Identifie les points forts et les points d'amélioration.

        Lettre de motivation:
        {letter_content}

        Contexte de la génération:
        Poste: {generation_request.job_title}
        Entreprise: {generation_request.company_name}
        Ton souhaité: {generation_request.tone.value}

        Format de la réponse:
        Score: [score]/10
        Points forts:
        - [Point fort 1]
        - [Point fort 2]
        Points d'amélioration:
        - [Amélioration 1]
        - [Amélioration 2]
        """
        return prompt.strip()

    def build_skills_suggestion_prompt(self, old_domain: str, new_domain: str) -> str:
        """
        Construit le prompt pour la suggestion de compétences transférables.
        """
        prompt = f"""
        Je suis en reconversion professionnelle. Mon ancien domaine d'activité était "{old_domain}" et je souhaite me reconvertir dans le domaine "{new_domain}".
        Liste 5 à 10 compétences clés de mon ancien domaine qui sont transférables et pertinentes pour mon nouveau domaine.
        Présente ces compétences sous forme de liste à puces, avec une brève explication de leur pertinence pour le nouveau domaine.
        Sois concis et utilise un langage professionnel.
        """
        return prompt.strip()
