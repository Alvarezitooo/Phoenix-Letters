"""Service d'optimisation de conversion Premium."""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging


@dataclass
class ConversionTrigger:
    """Déclencheur de conversion personnalisé."""
    trigger_type: str  # "usage_limit", "feature_attempt", "time_based"
    priority: int  # 1-5, 5 = highest
    message: str
    cta_text: str
    timing: Optional[str] = None  # "immediate", "delayed", "session_end"


class ConversionOptimizer:
    """Service d'optimisation des conversions Free → Premium."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.triggers = self._init_conversion_triggers()
    
    def _init_conversion_triggers(self) -> List[ConversionTrigger]:
        """Initialise les déclencheurs de conversion optimisés."""
        return [
            # Limite usage atteinte
            ConversionTrigger(
                trigger_type="usage_limit",
                priority=5,
                message="🚫 Limite atteinte ! Débloquez lettres illimitées maintenant",
                cta_text="🚀 Passer Premium (19€/mois)",
                timing="immediate"
            ),
            
            # Tentative feature Premium
            ConversionTrigger(
                trigger_type="feature_premium",
                priority=4,
                message="🔒 Cette fonctionnalité exclusive vous donnerait +89% de chances",
                cta_text="✨ Débloquer maintenant",
                timing="immediate"
            ),
            
            # Première lettre réussie
            ConversionTrigger(
                trigger_type="first_success",
                priority=3,
                message="🎉 Excellent ! Imaginez avec tous les outils Premium...",
                cta_text="🎯 Voir les outils Premium",
                timing="delayed"
            ),
            
            # Usage intensif
            ConversionTrigger(
                trigger_type="power_user",
                priority=4,
                message="💪 Vous maîtrisez Phoenix ! Prêt pour le niveau Pro ?",
                cta_text="🚀 Passer Pro",
                timing="session_end"
            )
        ]
    
    def get_optimal_trigger(
        self, 
        user_context: Dict[str, Any]
    ) -> Optional[ConversionTrigger]:
        """
        Retourne le meilleur déclencheur basé sur contexte utilisateur.
        
        Args:
            user_context: Contexte utilisateur (usage, actions, timing)
        Returns:
            Meilleur trigger ou None
        """
        
        applicable_triggers = []
        
        # Analyser contexte et filtrer triggers
        for trigger in self.triggers:
            if self._is_trigger_applicable(trigger, user_context):
                applicable_triggers.append(trigger)
        
        if not applicable_triggers:
            return None
        
        # Retourner trigger avec plus haute priorité
        return max(applicable_triggers, key=lambda t: t.priority)
    
    def _is_trigger_applicable(
        self, 
        trigger: ConversionTrigger, 
        user_context: Dict[str, Any]
    ) -> bool:
        """Vérifie si trigger applicable au contexte."""
        
        trigger_type = trigger.trigger_type
        
        if trigger_type == "usage_limit":
            return user_context.get("remaining_letters", 1) <= 0
        
        elif trigger_type == "feature_premium":
            return user_context.get("attempted_premium_feature", False)
        
        elif trigger_type == "first_success":
            return (
                user_context.get("letters_generated", 0) == 1 and
                user_context.get("generation_successful", False)
            )
        
        elif trigger_type == "power_user":
            return (
                user_context.get("session_actions", 0) >= 5 and
                user_context.get("time_spent_minutes", 0) >= 10
            )
        
        return False
    
    def get_personalized_pricing(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Retourne pricing personnalisé basé sur profil utilisateur."""
        
        base_price = 19
        original_price = 29
        discount_pct = 33
        
        # Personnalisation basée sur contexte
        if user_context.get("is_student", False):
            base_price = 15
            discount_pct = 48  # Réduction étudiante
        
        elif user_context.get("reconversion_urgency", "normal") == "high":
            # Pricing urgence avec social proof
            base_price = 19
            urgency_message = "⏰ 48h pour postuler ? Débloquez TOUT maintenant !"
        
        return {
            "current_price": base_price,
            "original_price": original_price,
            "discount_percent": discount_pct,
            "currency": "€",
            "billing": "mois",
            "urgency_message": user_context.get("urgency_message"),
            "social_proof": f"{user_context.get('active_users', 2847)}+ professionnels nous font confiance"
        }
    
    def get_dynamic_testimonial(self, user_context: Dict[str, Any]) -> Dict[str, str]:
        """Retourne témoignage personnalisé selon profil."""
        
        target_sector = user_context.get("target_sector", "Tech")
        
        testimonials = {
            "Tech": {
                "text": "Grâce à Phoenix Premium, transition Marketing → Tech réussie en 3 semaines !",
                "author": "Sarah M. - DevOps Engineer",
                "metric": "3 entretiens techniques décrochés"
            },
            "Marketing": {
                "text": "L'ATS Analyzer m'a fait passer tous les filtres RH automatiques.",
                "author": "Thomas R. - Marketing Manager",
                "metric": "89% de taux de réponse"
            },
            "Finance": {
                "text": "Phoenix m'a aidé à valoriser mes compétences transférables parfaitement.",
                "author": "Julie L. - Analyste Financier",
                "metric": "CDI décroché en 2 mois"
            }
        }
        
        return testimonials.get(target_sector, testimonials["Tech"])
    
    def calculate_roi_message(self, user_context: Dict[str, Any]) -> str:
        """Calcule message ROI personnalisé."""
        
        monthly_cost = 19
        potential_salary = user_context.get("target_salary", 45000)
        monthly_salary = potential_salary / 12
        
        roi_multiplier = monthly_salary / monthly_cost
        
        return (
            f"💰 ROI: {monthly_cost}€ investis = {monthly_salary:,.0f}€/mois potentiels "
            f"(x{roi_multiplier:.0f} retour sur investissement)"
        )
    
    def get_conversion_analytics(self) -> Dict[str, Any]:
        """Retourne analytics de conversion pour optimisation."""
        
        # Mock data - à remplacer par vraies métriques
        return {
            "conversion_rate_overall": 12.3,
            "conversion_rate_by_trigger": {
                "usage_limit": 18.5,
                "feature_premium": 15.2,
                "first_success": 8.7,
                "power_user": 22.1
            },
            "best_performing_cta": "🚀 Passer Premium (19€/mois)",
            "optimal_timing": "immediate",
            "top_converting_features": ["Mirror Match", "ATS Analyzer"],
            "user_segments": {
                "urgent_job_seekers": 25.4,
                "career_changers": 14.8,
                "students": 9.2
            }
        }