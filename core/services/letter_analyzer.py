"""Service structuré pour l'analyse de lettres de motivation."""
import re
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass

from core.entities.letter import Letter, UserTier
from shared.interfaces.ai_interface import AIServiceInterface
from shared.interfaces.prompt_interface import PromptServiceInterface
from shared.exceptions.specific_exceptions import LetterGenerationError, AIServiceError

logger = logging.getLogger(__name__)


@dataclass
class LetterAnalysisResult:
    """Résultat structuré de l'analyse d'une lettre."""
    score: Optional[float] = None
    strengths: List[str] = None
    improvements: List[str] = None
    raw_analysis: str = ""
    
    def __post_init__(self):
        """Initialise les listes vides si None."""
        if self.strengths is None:
            self.strengths = []
        if self.improvements is None:
            self.improvements = []


class LetterAnalyzer:
    """Service d'analyse structurée des lettres de motivation."""
    
    # Configuration d'analyse
    ANALYSIS_TEMPERATURE = 0.3  # Plus déterministe
    MAX_ANALYSIS_TOKENS = 1000
    
    def __init__(
        self,
        ai_service: AIServiceInterface,
        prompt_service: PromptServiceInterface
    ):
        """
        Initialise l'analyseur de lettres.
        
        Args:
            ai_service: Service d'IA pour l'analyse
            prompt_service: Service de construction des prompts
        """
        self._ai_service = ai_service
        self._prompt_service = prompt_service
        
        # Pré-compilation des patterns regex pour performance
        self._score_pattern = re.compile(r'Score:\s*(\d+(?:\.\d+)?)/10', re.IGNORECASE)
        self._strengths_pattern = re.compile(
            r'Points forts:(.*?)(?:Points d\'amélioration:|$)',
            re.DOTALL | re.IGNORECASE
        )
        self._improvements_pattern = re.compile(
            r'Points d\'amélioration:(.*?)(?:Score:|$)',
            re.DOTALL | re.IGNORECASE
        )
        
        logger.info("LetterAnalyzer initialized")
    
    def analyze_letter(self, letter: Letter, user_tier: UserTier) -> LetterAnalysisResult:
        """
        Analyse une lettre de motivation de manière structurée.
        
        Args:
            letter: Lettre à analyser
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            LetterAnalysisResult: Résultat structuré de l'analyse
            
        Raises:
            LetterGenerationError: Si l'analyse échoue
        """
        try:
            # Construction du prompt d'analyse
            analysis_prompt = self._prompt_service.build_analysis_prompt(
                letter.content,
                letter.generation_request
            )
            
            # Analyse via IA avec paramètres optimisés
            raw_analysis = self._ai_service.generate_content(
                prompt=analysis_prompt,
                user_tier=user_tier,
                max_tokens=self.MAX_ANALYSIS_TOKENS,
                temperature=self.ANALYSIS_TEMPERATURE
            )
            
            # Structuration du résultat
            result = self._parse_analysis_result(raw_analysis)
            
            logger.info(
                f"Letter analysis completed",
                extra={
                    "user_tier": user_tier.value,
                    "score": result.score,
                    "strengths_count": len(result.strengths),
                    "improvements_count": len(result.improvements)
                }
            )
            
            return result
            
        except AIServiceError as e:
            logger.error(f"AI service error during analysis: {e}")
            raise LetterGenerationError(f"Erreur lors de l'analyse: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in letter analysis: {e}")
            raise LetterGenerationError(f"Erreur système lors de l'analyse: {str(e)}")
    
    def _parse_analysis_result(self, raw_analysis: str) -> LetterAnalysisResult:
        """
        Parse le résultat brut de l'analyse en structure typée.
        
        Args:
            raw_analysis: Résultat brut de l'IA
            
        Returns:
            LetterAnalysisResult: Résultat structuré
        """
        if not raw_analysis or not isinstance(raw_analysis, str):
            logger.warning("Empty or invalid analysis result")
            return LetterAnalysisResult(raw_analysis=raw_analysis or "")
        
        result = LetterAnalysisResult(raw_analysis=raw_analysis)
        
        try:
            # Extraction du score
            result.score = self._extract_score(raw_analysis)
            
            # Extraction des points forts
            result.strengths = self._extract_strengths(raw_analysis)
            
            # Extraction des améliorations
            result.improvements = self._extract_improvements(raw_analysis)
            
        except Exception as e:
            logger.warning(f"Error parsing analysis result: {e}")
            # En cas d'erreur de parsing, on garde le résultat brut
        
        return result
    
    def _extract_score(self, analysis: str) -> Optional[float]:
        """
        Extrait le score de l'analyse de manière sécurisée.
        
        Args:
            analysis: Texte d'analyse
            
        Returns:
            Optional[float]: Score extrait ou None
        """
        try:
            match = self._score_pattern.search(analysis)
            if match:
                score = float(match.group(1))
                # Validation du score (doit être entre 0 et 10)
                if 0 <= score <= 10:
                    return score
                else:
                    logger.warning(f"Invalid score value: {score}")
        except (ValueError, AttributeError) as e:
            logger.debug(f"Score extraction failed: {e}")
        return None
    
    def _extract_strengths(self, analysis: str) -> List[str]:
        """
        Extrait les points forts de l'analyse.
        
        Args:
            analysis: Texte d'analyse
            
        Returns:
            List[str]: Liste des points forts
        """
        return self._extract_bullet_points(analysis, self._strengths_pattern)
    
    def _extract_improvements(self, analysis: str) -> List[str]:
        """
        Extrait les points d'amélioration de l'analyse.
        
        Args:
            analysis: Texte d'analyse
            
        Returns:
            List[str]: Liste des améliorations
        """
        return self._extract_bullet_points(analysis, self._improvements_pattern)
    
    def _extract_bullet_points(self, text: str, pattern: re.Pattern) -> List[str]:
        """
        Extrait des points sous forme de liste à partir d'un pattern regex.
        
        Args:
            text: Texte à analyser
            pattern: Pattern regex compilé
            
        Returns:
            List[str]: Liste des points extraits
        """
        try:
            match = pattern.search(text)
            if match:
                section_text = match.group(1).strip()
                if section_text:
                    # Split par lignes et nettoyage
                    lines = section_text.split('\n')
                    points = []
                    for line in lines:
                        cleaned_line = line.strip().lstrip('- •*').strip()
                        if cleaned_line and len(cleaned_line) > 3:  # Évite les lignes vides/très courtes
                            points.append(cleaned_line)
                    return points
        except Exception as e:
            logger.debug(f"Bullet points extraction failed: {e}")
        return []
    
    def get_analysis_summary(self, result: LetterAnalysisResult) -> Dict[str, any]:
        """
        Génère un résumé de l'analyse pour l'affichage.
        
        Args:
            result: Résultat d'analyse
            
        Returns:
            Dict: Résumé formaté
        """
        return {
            "score": result.score,
            "score_display": f"{result.score}/10" if result.score else "Non disponible",
            "strengths_count": len(result.strengths),
            "improvements_count": len(result.improvements),
            "has_structured_data": bool(result.score or result.strengths or result.improvements),
            "analysis_quality": self._assess_analysis_quality(result)
        }
    
    def _assess_analysis_quality(self, result: LetterAnalysisResult) -> str:
        """Évalue la qualité de l'analyse effectuée."""
        if result.score and result.strengths and result.improvements:
            return "complete"
        elif result.score or result.strengths or result.improvements:
            return "partial"
        else:
            return "basic"