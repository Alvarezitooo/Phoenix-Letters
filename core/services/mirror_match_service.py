"""Service Mirror Match - Analyse de culture d'entreprise."""
import logging
import re
from typing import Dict, List, Optional
from dataclasses import asdict

from core.entities.letter import CompanyCulture, UserTier
from shared.interfaces.ai_interface import AIServiceInterface
from infrastructure.security.input_validator import InputValidator

logger = logging.getLogger(__name__)

class MirrorMatchService:
    """Service d'analyse de culture d'entreprise pour adaptation du ton."""
    
    def __init__(self, ai_client: AIServiceInterface, input_validator: InputValidator):
        self.ai_client = ai_client
        self.input_validator = input_validator
        
        # Base de données des indicateurs culturels
        self.cultural_keywords = {
            "startup": ["agile", "innovation", "disruptif", "pivot", "scale", "lean", "mvp"],
            "corporate": ["excellence", "conformité", "processus", "hiérarchie", "gouvernance"],
            "tech": ["digital", "data", "ia", "algorithme", "api", "cloud", "devops"],
            "creative": ["créatif", "design", "brand", "storytelling", "visuel", "artistique"],
            "consulting": ["stratégie", "optimisation", "transformation", "expertise", "conseil"],
            "finance": ["roi", "kpi", "budget", "risque", "compliance", "audit", "performance"]
        }
        
        self.communication_indicators = {
            "formal": ["madame", "monsieur", "veuillez", "cordialement", "respectueusement"],
            "casual": ["salut", "bonjour", "sympa", "cool", "équipe", "ambiance"],
            "innovative": ["disruption", "innovation", "révolution", "transformation", "futur"],
            "traditional": ["tradition", "histoire", "expérience", "établi", "référence"]
        }

    def analyze_company_culture(self, company_name: str, job_offer: str, 
                              additional_info: Optional[str] = None, user_tier: UserTier = UserTier.FREE) -> CompanyCulture:
        """
        Analyse la culture d'entreprise à partir de l'offre d'emploi.
        
        Args:
            company_name: Nom de l'entreprise
            job_offer: Contenu de l'offre d'emploi
            additional_info: Informations supplémentaires (site web, etc.)
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            CompanyCulture: Analyse complète de la culture
        """
        if user_tier == UserTier.FREE:
            logger.info("Mirror Match is a premium feature. Returning default for Free user.")
            return self._get_default_culture(company_name, is_premium_feature=True)

        try:
            logger.info(f"Analyzing company culture for: {company_name}")
            
            # Validation des entrées
            self.input_validator.sanitize_text_input(company_name)
            self.input_validator.sanitize_text_input(job_offer)
            
            # Analyse basique par mots-clés
            basic_analysis = self._analyze_keywords(job_offer)
            
            # Analyse IA approfondie
            ai_analysis = self._get_ai_cultural_analysis(company_name, job_offer, additional_info, user_tier)
            
            # Fusion des analyses
            culture = self._merge_analyses(company_name, basic_analysis, ai_analysis)
            
            logger.info(f"Culture analysis completed for {company_name} - Score: {culture.confidence_score}")
            return culture
            
        except Exception as e:
            logger.error(f"Error analyzing company culture: {e}")
            return self._get_default_culture(company_name)

    def _analyze_keywords(self, job_offer: str) -> Dict:
        """Analyse basée sur les mots-clés."""
        job_lower = job_offer.lower()
        
        # Détection du secteur
        industry_scores = {}
        for industry, keywords in self.cultural_keywords.items():
            score = sum(1 for keyword in keywords if keyword in job_lower)
            if score > 0:
                industry_scores[industry] = score
        
        dominant_industry = max(industry_scores.items(), key=lambda x: x[1])[0] if industry_scores else "general"
        
        # Détection du style de communication
        comm_scores = {}
        for style, indicators in self.communication_indicators.items():
            score = sum(1 for indicator in indicators if indicator in job_lower)
            if score > 0:
                comm_scores[style] = score
        
        communication_style = max(comm_scores.items(), key=lambda x: x[1])[0] if comm_scores else "formal"
        
        # Détection de la taille d'entreprise
        company_size = self._detect_company_size(job_offer)
        
        # Détection environnement de travail
        work_environment = self._detect_work_environment(job_offer)
        
        return {
            "industry": dominant_industry,
            "communication_style": communication_style,
            "company_size": company_size,
            "work_environment": work_environment,
            "keyword_confidence": len(industry_scores) / 10.0  # Score de confiance basique
        }

    def _get_ai_cultural_analysis(self, company_name: str, job_offer: str, 
                                additional_info: Optional[str], user_tier: UserTier) -> Dict:
        """Utilise l'IA pour une analyse culturelle approfondie."""
        prompt = f"""
        Analysez la culture d'entreprise de {company_name} basée sur cette offre d'emploi :
        
        OFFRE D'EMPLOI:
        {job_offer}
        
        INFORMATIONS SUPPLÉMENTAIRES:
        {additional_info or "Aucune"}
        
        Analysez et retournez UNIQUEMENT un JSON avec cette structure exacte :
        {{
            "values": ["valeur1", "valeur2", "valeur3"],
            "leadership_style": "hierarchical|flat|collaborative",
            "innovation_level": "conservative|moderate|innovative",
            "cultural_keywords": ["mot1", "mot2", "mot3"],
            "tone_recommendations": ["conseil1", "conseil2"],
            "confidence_score": 0.85
        }}
        
        Basez votre analyse sur :
        - Le vocabulaire utilisé
        - Les avantages mentionnés
        - Les qualités recherchées
        - Le style de rédaction de l'offre
        """
        
        try:
            response = self.ai_client.generate_content(prompt=prompt, temperature=0.3, max_tokens=500, user_tier=user_tier)
            # Parser la réponse JSON (à implémenter selon le format de réponse)
            return self._parse_ai_response(response)
        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            return {"confidence_score": 0.3}

    def _merge_analyses(self, company_name: str, basic: Dict, ai: Dict) -> CompanyCulture:
        """Fusionne les analyses basique et IA."""
        return CompanyCulture(
            company_name=company_name,
            industry=basic.get("industry", "general"),
            company_size=basic.get("company_size"),
            values=ai.get("values", ["professionnalisme", "qualité", "innovation"]),
            communication_style=basic.get("communication_style", "formal"),
            work_environment=basic.get("work_environment", "traditional"),
            tone_recommendations=ai.get("tone_recommendations", ["Ton professionnel adapté"]),
            cultural_keywords=ai.get("cultural_keywords", []),
            leadership_style=ai.get("leadership_style", "hierarchical"),
            innovation_level=ai.get("innovation_level", "moderate"),
            confidence_score=min(basic.get("keyword_confidence", 0.3) + ai.get("confidence_score", 0.3), 1.0)
        )

    def _detect_company_size(self, job_offer: str) -> str:
        """Détecte la taille approximative de l'entreprise."""
        job_lower = job_offer.lower()
        
        if any(word in job_lower for word in ["startup", "scale-up", "jeune pousse"]):
            return "startup"
        elif any(word in job_lower for word in ["multinational", "groupe", "leader mondial"]):
            return "large"
        elif any(word in job_lower for word in ["pme", "tpe", "familial"]):
            return "small"
        else:
            return "medium"

    def _detect_work_environment(self, job_offer: str) -> str:
        """Détecte l'environnement de travail."""
        job_lower = job_offer.lower()
        
        if any(word in job_lower for word in ["télétravail", "remote", "distance"]):
            return "remote"
        elif any(word in job_lower for word in ["hybride", "flexible"]):
            return "hybrid"
        elif any(word in job_lower for word in ["startup", "open space", "agile"]):
            return "startup"
        else:
            return "corporate"

    def _parse_ai_response(self, response: str) -> Dict:
        """Parse la réponse IA en JSON."""
        try:
            import json
            # Nettoyer la réponse si nécessaire
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:-3]
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {"confidence_score": 0.3}

    def _get_default_culture(self, company_name: str, is_premium_feature: bool = False) -> CompanyCulture:
        """Retourne une analyse culturelle par défaut."""
        if is_premium_feature:
            return CompanyCulture(
                company_name=company_name,
                industry="N/A",
                values=["Fonctionnalité Premium"],
                communication_style="N/A",
                work_environment="N/A",
                tone_recommendations=["Cette fonctionnalité est réservée aux utilisateurs Premium.", "Passez Premium pour débloquer l'analyse de culture d'entreprise."],
                cultural_keywords=["Premium"],
                confidence_score=0.0
            )
        return CompanyCulture(
            company_name=company_name,
            industry="general",
            values=["professionnalisme", "qualité", "engagement"],
            communication_style="formal",
            work_environment="traditional",
            tone_recommendations=["Utilisez un ton professionnel et respectueux"],
            cultural_keywords=["professionnel", "qualité", "engagement"],
            confidence_score=0.2
        )

    def get_tone_adaptation_suggestions(self, culture: CompanyCulture) -> List[str]:
        """Génère des suggestions d'adaptation du ton basées sur la culture."""
        suggestions = []
        
        if culture.communication_style == "casual":
            suggestions.extend([
                "Adoptez un ton plus décontracté et accessible",
                "Utilisez 'vous' plutôt que des formules très formelles",
                "Montrez votre personnalité et votre enthousiasme"
            ])
        elif culture.communication_style == "formal":
            suggestions.extend([
                "Maintenez un ton professionnel et respectueux",
                "Utilisez des formules de politesse appropriées",
                "Structurez clairement vos arguments"
            ])
        
        if culture.innovation_level == "innovative":
            suggestions.append("Mettez en avant votre capacité d'adaptation et d'innovation")
        
        if culture.work_environment == "startup":
            suggestions.extend([
                "Montrez votre agilité et votre capacité à travailler en autonomie",
                "Mentionnez votre expérience avec les méthodologies agiles"
            ])
        
        return suggestions[:5]  # Limiter à 5 suggestions maximum