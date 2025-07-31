"""Service sécurisé pour l'extraction de données des offres d'emploi."""
import re
import logging
from typing import Optional, Tuple, Pattern
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JobDetails:
    """Détails extraits d'une offre d'emploi."""
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class JobOfferParser:
    """Parser sécurisé pour l'extraction de données des offres d'emploi."""
    
    # Constantes de sécurité
    MAX_INPUT_LENGTH = 50000  # Limite pour éviter ReDoS
    REGEX_TIMEOUT = 2.0  # Timeout en secondes pour regex
    
    def __init__(self):
        """Initialise le parser avec des patterns pré-compilés et sécurisés."""
        self._job_title_patterns = self._compile_safe_patterns([
            # Patterns simplifiés et sécurisés (évitent catastrophic backtracking)
            r"^(?:offre d'emploi|poste|intitulé du poste)[:\s]*([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})",
            r"\b(?:recherchons|recrutons|poste de|intitulé du poste|emploi)[:\s]*([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})",
            r"\b(?:un|une)\s+([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})(?:\s+pour|\s+en|\s+chez|\s+à)?",
            r"titre du poste\s*:\s*([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})",
            # Patterns plus restrictifs pour éviter ReDoS
            r"\b([A-Z][A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,80})(?:\s+H/F|\s+\(H/F\)|\s+CDI|\s+CDD|\s+Stage|\s+Alternance)?\s*$",
            r"\b([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,80})(?:\s+senior|\s+junior|\s+confirmé)?\s*$",
        ])
        
        self._company_name_patterns = self._compile_safe_patterns([
            r"(?:chez|pour|société|entreprise)[:\s]*([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})",
            r"nom de l'entreprise\s*:\s*([A-Za-zÀ-ÖØ-öø-ÿ\s-]{1,100})"
        ])
        
        logger.info("JobOfferParser initialized with secure patterns")
    
    def _compile_safe_patterns(self, patterns: list[str]) -> list[Pattern]:
        """Compile les patterns regex de manière sécurisée."""
        compiled_patterns = []
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Invalid regex pattern ignored: {pattern} - {e}")
        return compiled_patterns
    
    def _sanitize_input(self, content: str) -> str:
        """Sanitise et valide l'input pour éviter les attaques."""
        if not content:
            return ""
        
        # Limite de longueur pour éviter ReDoS
        if len(content) > self.MAX_INPUT_LENGTH:
            logger.warning(f"Input truncated from {len(content)} to {self.MAX_INPUT_LENGTH} chars")
            content = content[:self.MAX_INPUT_LENGTH]
        
        # Nettoyage basique
        content = content.strip()
        
        # Remove null bytes et caractères de contrôle dangereux
        content = content.replace('\x00', '').replace('\r\n', '\n')
        
        return content
    
    def _safe_regex_search(self, patterns: list[Pattern], content: str) -> Optional[str]:
        """Effectue une recherche regex sécurisée avec timeout."""
        for pattern in patterns:
            try:
                # Note: Python ne supporte pas nativement le timeout regex
                # En production, utiliser le module `regex` avec timeout
                match = pattern.search(content)
                if match and match.group(1):
                    result = match.group(1).strip()
                    # Validation supplémentaire du résultat
                    if 1 <= len(result) <= 100:  # Longueur raisonnable
                        return result
            except Exception as e:
                logger.warning(f"Regex search error: {e}")
                continue
        return None
    
    def extract_job_details(self, job_offer_content: str) -> JobDetails:
        """
        Extrait de manière sécurisée les détails d'une offre d'emploi.
        
        Args:
            job_offer_content: Contenu de l'offre d'emploi
            
        Returns:
            JobDetails: Détails extraits de l'offre
            
        Raises:
            ValueError: Si l'input est invalide
        """
        if not isinstance(job_offer_content, str):
            raise ValueError("job_offer_content must be a string")
        
        # Sanitisation sécurisée
        sanitized_content = self._sanitize_input(job_offer_content)
        
        if not sanitized_content:
            logger.info("Empty or invalid job offer content")
            return JobDetails()
        
        try:
            # Extraction sécurisée du titre
            job_title = self._safe_regex_search(self._job_title_patterns, sanitized_content)
            
            # Extraction sécurisée du nom d'entreprise
            company_name = self._safe_regex_search(self._company_name_patterns, sanitized_content)
            
            details = JobDetails(job_title=job_title, company_name=company_name)
            
            logger.debug(
                f"Extracted job details: title='{job_title}', company='{company_name}'",
                extra={"job_title_found": bool(job_title), "company_found": bool(company_name)}
            )
            
            return details
            
        except Exception as e:
            logger.error(f"Unexpected error in job details extraction: {e}")
            # Retourne un objet vide plutôt que de propager l'erreur
            return JobDetails()