"""Tests unitaires pour le service de génération de lettres."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.services.letter_service import LetterService
from core.entities.letter import GenerationRequest, ToneType, UserTier, Letter
from shared.exceptions.specific_exceptions import LetterGenerationError, ValidationError
from shared.interfaces.ai_interface import AIServiceInterface
from shared.interfaces.monitoring_interface import MonitoringInterface
from shared.interfaces.validation_interface import ValidationServiceInterface
from shared.interfaces.prompt_interface import PromptServiceInterface

class TestLetterService:
    """Tests pour LetterService."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock du service IA."""
        mock = Mock(spec=AIServiceInterface)
        mock.generate_content.side_effect = lambda prompt, user_tier, max_tokens, temperature: f"Generated content for prompt: {prompt}"
        return mock
    
    @pytest.fixture
    def mock_validation_service(self):
        """Mock du service de validation."""
        mock = Mock(spec=ValidationServiceInterface)
        def validate_side_effect(request):
            if not request.cv_content.strip():
                raise ValidationError("Le contenu du CV est requis")
            if not request.job_offer_content.strip():
                raise ValidationError("Le contenu de l'offre d'emploi est requis")
            if len(request.cv_content) > 50000:
                raise ValidationError("Le CV est trop long (max 50,000 caractères)")
        mock.validate_generation_request.side_effect = validate_side_effect
        return mock

    @pytest.fixture
    def mock_prompt_service(self):
        """Mock du service de prompt."""
        mock = Mock(spec=PromptServiceInterface)
        def build_letter_prompt_side_effect(request):
            prompt = f"Prompt for {request.tone.value} letter."
            if request.is_career_change:
                prompt += f" Career change from {request.old_domain} to {request.new_domain} with skills {request.transferable_skills}."
            prompt += f" CV: {request.cv_content[:50]}... Job Offer: {request.job_offer_content[:50]}..."
            return prompt
        mock.build_letter_prompt.side_effect = build_letter_prompt_side_effect
        mock.build_analysis_prompt.return_value = "Generated analysis prompt"
        return mock

    @pytest.fixture
    def mock_session_manager(self):
        """Mock du gestionnaire de session."""
        mock = Mock()
        mock.get.return_value = 0  # Valeurs par défaut pour les tests
        mock.set.return_value = None
        return mock
    
    @pytest.fixture
    def letter_service(self, mock_ai_service, mock_validation_service, mock_prompt_service, mock_session_manager):
        """Instance du service de lettres avec session manager."""
        return LetterService(mock_ai_service, mock_validation_service, mock_prompt_service, mock_session_manager)
    
    @pytest.fixture
    def valid_request(self):
        """Requête valide de génération."""
        return GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            job_title="Développeur Python",
            company_name="TechCorp",
            tone=ToneType.FORMAL,
            user_tier=UserTier.FREE,
            is_career_change=False
        )
    
    def test_generate_letter_success(self, letter_service, valid_request, mock_ai_service):
        """Test de génération réussie."""
        # Arrange
        user_id = "test_user_123"
        # Le contenu sera généré par le mock_ai_service selon sa configuration
        # Nous utilisons directement le retour du mock pour l'assertion
        
        # Act
        result = letter_service.generate_letter(valid_request, user_id)
        
        # Assert
        assert isinstance(result, Letter)
        assert result.user_id == user_id
        assert result.generation_request == valid_request
        assert isinstance(result.created_at, datetime)
        assert result.content is not None  # Le contenu doit être généré
        
        # Vérification des appels
        mock_ai_service.generate_content.assert_called_once()
    
    def test_generate_letter_empty_cv_raises_validation_error(self, letter_service):
        """Test avec CV vide lève ValidationError."""
        # Arrange
        invalid_request = GenerationRequest(
            cv_content="",  # CV vide
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            job_title="Développeur",
            company_name="Test Corp",
            tone=ToneType.FORMAL,
            user_tier=UserTier.FREE
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            letter_service.generate_letter(invalid_request, "test_user")
    
    def test_generate_letter_empty_job_offer_raises_validation_error(self, letter_service):
        """Test avec offre vide lève ValidationError."""
        # Arrange
        invalid_request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="",  # Offre vide
            job_title="Développeur",
            company_name="Test Corp",
            tone=ToneType.FORMAL,
            user_tier=UserTier.FREE
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            letter_service.generate_letter(invalid_request, "test_user")
    
    def test_generate_letter_cv_too_long_raises_validation_error(self, letter_service):
        """Test avec CV trop long lève ValidationError."""
        # Arrange
        invalid_request = GenerationRequest(
            cv_content="x" * 50001,  # CV trop long
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            job_title="Développeur",
            company_name="Test Corp",
            tone=ToneType.FORMAL,
            user_tier=UserTier.FREE
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            letter_service.generate_letter(invalid_request, "test_user")
    
    def test_generate_letter_career_change_prompt(self, letter_service, mock_ai_service):
        """Test de génération avec reconversion."""
        # Arrange
        career_change_request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            job_title="Expert Cybersécurité",
            company_name="SecureTech",
            tone=ToneType.DYNAMIC,
            user_tier=UserTier.PREMIUM,
            is_career_change=True,
            old_domain="Marketing",
            new_domain="Cybersécurité",
            transferable_skills="Communication, Gestion de projet"
        )
        
        # Act
        letter_service.generate_letter(career_change_request, "test_user")
        
        # Assert
        mock_ai_service.generate_content.assert_called_once()
        call_args = mock_ai_service.generate_content.call_args
        prompt = call_args[1]['prompt']
        
        # Vérifications du prompt de reconversion
        assert "career change" in prompt.lower()
        assert "Marketing" in prompt
        assert "Cybersécurité" in prompt
        assert "Communication, Gestion de projet" in prompt
    
    def test_generate_letter_ai_service_error_raises_letter_generation_error(
        self, letter_service, valid_request, mock_ai_service
    ):
        """Test avec erreur du service IA lève LetterGenerationError."""
        # Arrange
        from shared.exceptions.specific_exceptions import AIServiceError
        mock_ai_service.generate_content.side_effect = AIServiceError("API Error")
        
        # Act & Assert
        with pytest.raises(LetterGenerationError, match="Erreur du service IA"):
            letter_service.generate_letter(valid_request, "test_user")
    
    def test_analyze_letter_success_premium(self, letter_service):
        """Test d'analyse de lettre réussie pour utilisateur Premium."""
        # Arrange
        letter = Letter(
            content="Contenu de lettre à analyser avec suffisamment de texte pour être valide",
            generation_request=GenerationRequest(
                cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
                job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
                job_title="Analyste",
                company_name="AnalysisCorp",
                tone=ToneType.FORMAL,
                user_tier=UserTier.PREMIUM  # Utilisateur Premium pour accès analyse
            ),
            created_at=datetime.now(),
            user_id="test_user"
        )
        
        # Act
        from core.services.letter_analyzer import LetterAnalysisResult
        analysis = letter_service.analyze_letter(letter, UserTier.PREMIUM)
        
        # Assert - Structure refactorisée
        assert isinstance(analysis, LetterAnalysisResult)
        assert analysis.raw_analysis is not None
        assert isinstance(analysis.strengths, list)
        assert isinstance(analysis.improvements, list)
    
    def test_analyze_letter_free_user_denied(self, letter_service):
        """Test d'analyse refusée pour utilisateur FREE."""
        # Arrange
        letter = Letter(
            content="Contenu de lettre",
            generation_request=GenerationRequest(
                cv_content="CV content",
                job_offer_content="Job offer content",
                job_title="Assistant",
                company_name="TestCorp",
                tone=ToneType.FORMAL,
                user_tier=UserTier.FREE
            ),
            created_at=datetime.now(),
            user_id="test_user"
        )
        
        # Act & Assert
        with pytest.raises(ValidationError, match="réservée aux utilisateurs Premium"):
            letter_service.analyze_letter(letter, UserTier.FREE)
    
    @pytest.mark.parametrize("user_tier", [
        UserTier.FREE,
        UserTier.PREMIUM,
        UserTier.PREMIUM_PLUS
    ])
    def test_prompt_quality_by_tier(self, letter_service, mock_ai_service, user_tier):
        """Test de la qualité du prompt selon le tier utilisateur."""
        # Arrange
        request = GenerationRequest(
            cv_content="""This is a valid CV content with enough text to satisfy the minimum length requirement of 50 characters. It contains various skills and experiences relevant for a job application.""",
            job_offer_content="""This is a valid job offer content with at least 20 characters, describing a position that requires specific skills and qualifications.""",
            job_title="Testeur",
            company_name="TestTech",
            tone=ToneType.FORMAL,
            user_tier=user_tier
        )
        
        # Act
        letter_service.generate_letter(request, "test_user")
        
        # Assert
        call_args = mock_ai_service.generate_content.call_args
        prompt = call_args[1]['prompt']
        assert request.tone.value in prompt

    def test_build_standard_prompt(self, letter_service, mock_prompt_service):
        """Test de la construction du prompt standard."""
        # Arrange
        request = GenerationRequest(
            cv_content="Mon CV standard.",
            job_offer_content="Offre d'emploi standard.",
            job_title="Employé",
            company_name="StandardCorp",
            tone=ToneType.SOBER,
            user_tier=UserTier.FREE,
            is_career_change=False
        )

        # Act
        prompt = letter_service._prompt_service.build_letter_prompt(request)

        # Assert
        mock_prompt_service.build_letter_prompt.assert_called_once_with(request)
        assert "Prompt for sobre letter." in prompt
        assert "CV: Mon CV standard.... Job Offer: Offre d'emploi standard...." in prompt
        assert "Career change" not in prompt