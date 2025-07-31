"""Client Google Gemini avec gestion d'erreurs robuste."""
import streamlit as st
import google.generativeai as genai
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from config.settings import Settings
from shared.interfaces.ai_interface import AIServiceInterface
from shared.exceptions.specific_exceptions import AIServiceError, RateLimitError
from core.entities.letter import UserTier

logger = logging.getLogger(__name__)

class GeminiClient(AIServiceInterface):
    """Client pour Google Gemini AI."""
    
    def __init__(self, settings: Settings):
        """Initialise le client Gemini."""
        self.settings = settings
        try:
            genai.configure(api_key=self.settings.google_api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise AIServiceError(f"Impossible d'initialiser le client IA: {e}")
    
    @st.cache_data(ttl=3600)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_content(
        _self, 
        prompt: str, 
        user_tier: UserTier,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Génère du contenu avec Gemini.
        
        Args:
            prompt: Prompt pour la génération
            user_tier: Niveau d'abonnement utilisateur
            max_tokens: Nombre maximum de tokens
            temperature: Température de génération
            
        Returns:
            str: Contenu généré
            
        Raises:
            AIServiceError: En cas d'erreur de génération
            RateLimitError: En cas de limite de débit atteinte
        """
        try:
            # Configuration selon le tier utilisateur
            generation_config = _self._get_generation_config(user_tier, max_tokens, temperature)
            
            # Validation du prompt
            if not prompt or len(prompt) < 10:
                raise AIServiceError("Prompt trop court ou vide")
            
            if len(prompt) > 100000:
                raise AIServiceError("Prompt trop long (max 100k caractères)")
            
            # Génération
            response = _self.model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": 30}
            )
            
            if not response.text:
                raise AIServiceError("Réponse vide du service IA")
            
            # Validation de la réponse
            if len(response.text) < 50:
                raise AIServiceError("Réponse trop courte du service IA")
            
            logger.info(f"Content generated successfully for {user_tier.value} user")
            return response.text.strip()
            
        except genai.types.BlockedPromptException:
            logger.warning("Prompt blocked by safety filters")
            raise AIServiceError("Contenu bloqué par les filtres de sécurité")
        
        except genai.types.StopCandidateException:
            logger.warning("Generation stopped by safety filters")
            raise AIServiceError("Génération interrompue par les filtres de sécurité")
        
        except Exception as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                logger.error(f"Rate limit exceeded: {e}")
                raise RateLimitError("Limite de débit API atteinte. Veuillez réessayer plus tard.")
            
            logger.error(f"Unexpected error in content generation: {e}")
            raise AIServiceError(f"Erreur inattendue du service IA: {e}")
    
    def _get_generation_config(
        self, 
        user_tier: UserTier, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Configure la génération selon le tier utilisateur."""
        base_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Configuration spécifique par tier
        if user_tier == UserTier.PREMIUM_PLUS:
            base_config.update({
                "temperature": 0.8,  # Plus créatif
                "top_p": 0.9,
                "top_k": 40
            })
        elif user_tier == UserTier.PREMIUM:
            base_config.update({
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 30
            })
        else:  # FREE
            base_config.update({
                "temperature": 0.6,  # Plus conservateur
                "top_p": 0.7,
                "top_k": 20
            })
        
        return base_config