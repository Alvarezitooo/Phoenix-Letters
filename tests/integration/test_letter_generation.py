"""Tests d'intégration pour la génération de lettres."""
import pytest
from unittest.mock import patch, Mock
import tempfile
import os

from core.services.letter_service import LetterService
from core.entities.letter import GenerationRequest, ToneType, UserTier
from infrastructure.ai.gemini_client import GeminiClient
from infrastructure.monitoring.performance_monitor import PerformanceMonitor
from shared.interfaces.validation_interface import ValidationServiceInterface
from shared.interfaces.prompt_interface import PromptServiceInterface

@pytest.mark.integration
class TestLetterGenerationIntegration:
    """Tests d'intégration pour la génération de lettres."""
    
    @pytest.fixture(scope="class")
    def letter_service_with_real_ai(self):
        """Service de lettres avec vrai client IA (si API key disponible)."""
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("GOOGLE_API_KEY not available for integration tests")
        
        ai_client = GeminiClient()
        # Pour les tests d'intégration, nous utilisons des mocks simples pour les services
        # de validation et de prompt, car l'objectif est de tester l'intégration avec l'IA.
        mock_validation_service = Mock(spec=ValidationServiceInterface)
        mock_validation_service.validate_generation_request.return_value = None
        mock_prompt_service = Mock(spec=PromptServiceInterface)
        mock_prompt_service.build_letter_prompt.return_value = "Generated prompt for integration test"
        mock_prompt_service.build_analysis_prompt.return_value = "Generated analysis prompt for integration test"
        return LetterService(ai_client, mock_validation_service, mock_prompt_service)
    
    def test_full_letter_generation_flow(self, letter_service_with_real_ai):
        """Test du flux complet de génération de lettre."""
        # Arrange
        request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            tone=ToneType.FORMAL,
            user_tier=UserTier.FREE,
            is_career_change=True,
            old_domain="Aide-soignant",
            new_domain="Cybersécurité",
            transferable_skills="Gestion de crise, Rigueur, Travail en équipe"
        )
        
        # Act
        letter = letter_service_with_real_ai.generate_letter(request, "integration_test_user")
        
        # Assert
        assert letter is not None
        assert len(letter.content) > 100
        assert "cybersécurité" in letter.content.lower() or "sécurité" in letter.content.lower()
        assert letter.user_id == "integration_test_user"
        
        # Vérifications spécifiques à la reconversion
        content_lower = letter.content.lower()
        assert any(skill.lower() in content_lower for skill in ["rigueur", "équipe", "crise"])
    
    def test_letter_analysis_integration(self, letter_service_with_real_ai):
        """Test d'intégration de l'analyse de lettre."""
        # Arrange - Générer d'abord une lettre
        request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            tone=ToneType.DYNAMIC,
            user_tier=UserTier.PREMIUM
        )
        
        letter = letter_service_with_real_ai.generate_letter(request, "test_user")
        
        # Act
        analysis = letter_service_with_real_ai.analyze_letter(letter)
        
        # Assert
        assert analysis is not None
        assert 0 <= analysis.ats_score <= 100
        assert 0 <= analysis.readability_score <= 100
        assert 0 <= analysis.keyword_match_score <= 100
        assert len(analysis.suggestions) > 0
        assert len(analysis.strengths) > 0
    
    @pytest.mark.parametrize("user_tier", [UserTier.FREE, UserTier.PREMIUM, UserTier.PREMIUM_PLUS])
    def test_generation_quality_by_tier(self, letter_service_with_real_ai, user_tier):
        """Test de la qualité de génération selon le tier."""
        # Arrange
        request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            tone=ToneType.STARTUP,
            user_tier=user_tier
        )
        
        # Act
        letter = letter_service_with_real_ai.generate_letter(request, f"test_user_{user_tier.value}")
        
        # Assert
        assert letter is not None
        assert len(letter.content) > 200  # Plus long pour les tiers supérieurs
        
        # Les tiers supérieurs devraient avoir du contenu plus sophistiqué
        if user_tier == UserTier.PREMIUM_PLUS:
            assert len(letter.content) > 300
        elif user_tier == UserTier.PREMIUM:
            assert len(letter.content) > 250