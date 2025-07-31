"""
Tests unitaires pour GeminiClient.

Quality Standards:
- Mocking complet et robuste de tenacity.retry
- Isolation totale des dépendances externes
- Tests focalisés sur comportements spécifiques
- Couverture complète des cas d'erreur
"""
import pytest
from unittest.mock import MagicMock, patch
import google.generativeai as genai

# Import des classes nécessaires après le patching potentiel
from infrastructure.ai.gemini_client import GeminiClient
from shared.exceptions.specific_exceptions import AIServiceError, RateLimitError
from core.entities.letter import UserTier

# Neutralise le décorateur retry pour tous les tests de ce module
# C'est une manière propre et globale de s'assurer que tenacity n'interfère pas.
patch('tenacity.retry', lambda *args, **kwargs: lambda func: func).start()

@pytest.fixture
def mock_settings():
    """Fixture pour mocker la configuration."""
    with patch('infrastructure.ai.gemini_client.Settings') as mock:
        instance = mock.return_value
        instance.google_api_key = 'test_api_key'
        yield mock

@pytest.fixture
def mock_genai_configure():
    """Fixture pour mocker genai.configure."""
    with patch('google.generativeai.configure') as mock:
        yield mock

@pytest.fixture
def mock_generative_model():
    """Fixture pour mocker genai.GenerativeModel."""
    with patch('google.generativeai.GenerativeModel') as mock:
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        # Réponse par défaut suffisamment longue pour passer la validation
        mock_response.text = "This is a sufficiently long generated text to pass validation."
        mock_model_instance.generate_content.return_value = mock_response
        mock.return_value = mock_model_instance
        yield mock_model_instance

@pytest.fixture
def gemini_client(mock_settings, mock_genai_configure, mock_generative_model):
    """
    Fixture principale qui assemble le client Gemini avec tous ses mocks.
    Cette fixture fournit une instance du client prête à l'emploi pour les tests.
    """
    client = GeminiClient()
    # Passe le mock du modèle pour que les tests puissent le manipuler
    client.model = mock_generative_model
    return client

class TestGeminiClient:
    """Tests pour GeminiClient avec une gestion propre des dépendances."""

    def test_initialization_success(self, gemini_client, mock_genai_configure, mock_settings):
        """Vérifie que l'initialisation se déroule comme prévu."""
        mock_genai_configure.assert_called_once_with(api_key='test_api_key')
        assert gemini_client.model is not None

    def test_initialization_fails_without_api_key(self, mock_settings):
        """Vérifie que l'initialisation échoue si la clé API est manquante."""
        # Arrange
        # Configure le mock pour simuler une clé API manquante
        with patch('infrastructure.ai.gemini_client.Settings') as mock_settings_class:
            instance = mock_settings_class.return_value
            # Simule le comportement de os.getenv qui retourne None
            instance.google_api_key = None
            # Simule l'erreur qui serait levée par from_env
            with patch('os.getenv', return_value=None):
                 with pytest.raises(AIServiceError, match="Impossible d'initialiser le client IA"):
                    GeminiClient()


    def test_generate_content_success(self, gemini_client):
        """Test de génération de contenu réussie."""
        prompt = "Test prompt with sufficient length"
        user_tier = UserTier.FREE
        result = gemini_client.generate_content(prompt, user_tier)

        gemini_client.model.generate_content.assert_called_once()
        call_kwargs = gemini_client.model.generate_content.call_args.kwargs
        assert call_kwargs['generation_config'] is not None
        assert result == "This is a sufficiently long generated text to pass validation."

    @pytest.mark.parametrize("error_message, exception_type", [
        ("Réponse vide du service IA", ""),
        ("Réponse vide du service IA", None),
        ("Réponse trop courte du service IA", "short text")
    ])
    def test_generate_content_invalid_responses(self, gemini_client, error_message, exception_type):
        """Teste la gestion des réponses invalides (vides, None, trop courtes)."""
        gemini_client.model.generate_content.return_value.text = exception_type
        prompt = "A valid prompt for testing purposes"
        with pytest.raises(AIServiceError, match=error_message):
            gemini_client.generate_content(prompt, UserTier.FREE)

    @pytest.mark.parametrize("prompt, error_match", [
        ("short", "Prompt trop court ou vide"),
        ("", "Prompt trop court ou vide"),
        ("x" * 100001, "Prompt trop long")
    ])
    def test_generate_content_invalid_prompts(self, gemini_client, prompt, error_match):
        """Teste la validation des prompts (trop courts, vides, trop longs)."""
        with pytest.raises(AIServiceError, match=error_match):
            gemini_client.generate_content(prompt, UserTier.FREE)

    @pytest.mark.parametrize("api_exception, expected_exception, error_match", [
        (Exception("Internal server error"), AIServiceError, "Erreur inattendue du service IA"),
        (Exception("429 Quota exceeded"), RateLimitError, "Limite de débit API atteinte"),
        (genai.types.BlockedPromptException("Blocked"), AIServiceError, "Contenu bloqué par les filtres de sécurité"),
        (genai.types.StopCandidateException("Stopped"), AIServiceError, "Génération interrompue par les filtres de sécurité")
    ])
    def test_generate_content_api_errors(self, gemini_client, api_exception, expected_exception, error_match):
        """Teste la gestion des différentes erreurs de l'API Gemini."""
        gemini_client.model.generate_content.side_effect = api_exception
        with pytest.raises(expected_exception, match=error_match):
            gemini_client.generate_content("a valid prompt", UserTier.FREE)

    @pytest.mark.parametrize("tier, expected_temp, expected_top_p, expected_top_k", [
        (UserTier.FREE, 0.6, 0.7, 20),
        (UserTier.PREMIUM, 0.7, 0.8, 30),
        (UserTier.PREMIUM_PLUS, 0.8, 0.9, 40)
    ])
    def test_generation_config_by_tier(self, gemini_client, tier, expected_temp, expected_top_p, expected_top_k):
        """Vérifie que la configuration de génération est correcte pour chaque tier."""
        gemini_client.generate_content("a valid prompt", tier)
        call_kwargs = gemini_client.model.generate_content.call_args.kwargs
        config = call_kwargs['generation_config']
        assert config['temperature'] == expected_temp
        assert config['top_p'] == expected_top_p
        assert config['top_k'] == expected_top_k

    def test_generate_content_with_custom_parameters(self, gemini_client):
        """Vérifie que les paramètres personnalisés écrasent bien les défauts du tier."""
        custom_temp = 0.99
        custom_tokens = 500
        
        gemini_client.generate_content(
            "a valid prompt",
            UserTier.PREMIUM, # Un tier avec ses propres réglages
            temperature=custom_temp,
            max_tokens=custom_tokens
        )

        call_kwargs = gemini_client.model.generate_content.call_args.kwargs
        config = call_kwargs['generation_config']
        
        # Vérifie que les paramètres passés ont bien écrasé ceux du tier PREMIUM
        assert config['temperature'] == custom_temp
        assert config['max_output_tokens'] == custom_tokens
        # Vérifie qu'une autre valeur du tier est toujours présente
        assert config['top_p'] == 0.8
