"""Service d'engagement utilisateur et relance conversion."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging


@dataclass
class EngagementTrigger:
    """Déclencheur d'engagement utilisateur."""
    trigger_id: str
    user_segment: str  # "new_user", "active_free", "churning", "limit_reached"
    message: str
    action_text: str
    timing_hours: int  # Heures après déclencheur
    priority: int  # 1-5


class UserEngagementService:
    """Service d'engagement et réactivation utilisateurs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engagement_triggers = self._init_triggers()
    
    def _init_triggers(self) -> List[EngagementTrigger]:
        """Initialise les déclencheurs d'engagement."""
        return [
            # Utilisateur nouveau (première visite)
            EngagementTrigger(
                trigger_id="welcome_new_user",
                user_segment="new_user", 
                message="🎉 Bienvenue ! Votre première lettre est prête à être générée",
                action_text="Commencer ma première lettre",
                timing_hours=0,
                priority=3
            ),
            
            # Limite atteinte il y a 24h
            EngagementTrigger(
                trigger_id="limit_reached_followup",
                user_segment="limit_reached",
                message="🔄 Prêt à continuer votre reconversion ? Débloquez maintenant !",
                action_text="Voir Premium (19€/mois)",
                timing_hours=24,
                priority=5
            ),
            
            # Utilisateur actif mais Free (5+ actions)
            EngagementTrigger(
                trigger_id="power_user_upgrade",
                user_segment="active_free",
                message="💪 Vous maîtrisez Phoenix ! Temps de passer au niveau Pro ?",
                action_text="Découvrir Premium",
                timing_hours=72,
                priority=4
            ),
            
            # Utilisateur inactif (7 jours sans visite)
            EngagementTrigger(
                trigger_id="win_back_inactive",
                user_segment="churning",
                message="🎯 Votre reconversion attend ! Reprenez où vous étiez",
                action_text="Reprendre ma reconversion",
                timing_hours=168,  # 7 jours
                priority=2
            )
        ]
    
    def get_user_segment(self, user_context: Dict[str, Any]) -> str:
        """Détermine le segment utilisateur pour engagement ciblé."""
        
        visits_count = user_context.get("visits_count", 0)
        letters_generated = user_context.get("letters_generated", 0)
        days_since_last_visit = user_context.get("days_since_last_visit", 0)
        limit_reached_recently = user_context.get("limit_reached_recently", False)
        session_actions = user_context.get("session_actions", 0)
        
        # Logique de segmentation
        if visits_count <= 1 and letters_generated == 0:
            return "new_user"
        
        elif limit_reached_recently:
            return "limit_reached"
        
        elif letters_generated >= 1 and session_actions >= 5:
            return "active_free"
        
        elif days_since_last_visit >= 7:
            return "churning"
        
        return "general"
    
    def get_engagement_message(self, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retourne message d'engagement personnalisé."""
        
        user_segment = self.get_user_segment(user_context)
        
        # Filtrer triggers applicables
        applicable_triggers = [
            t for t in self.engagement_triggers 
            if t.user_segment == user_segment
        ]
        
        if not applicable_triggers:
            return None
        
        # Prendre trigger avec plus haute priorité
        best_trigger = max(applicable_triggers, key=lambda t: t.priority)
        
        return {
            "trigger_id": best_trigger.trigger_id,
            "message": best_trigger.message,
            "action_text": best_trigger.action_text,
            "segment": user_segment,
            "priority": best_trigger.priority,
            "personalization": self._get_personalization(user_context)
        }
    
    def _get_personalization(self, user_context: Dict[str, Any]) -> Dict[str, str]:
        """Ajoute personnalisation basée sur contexte."""
        
        target_role = user_context.get("target_role", "votre rôle cible")
        current_sector = user_context.get("current_sector", "votre secteur")
        
        return {
            "target_role": target_role,
            "current_sector": current_sector,
            "progress_metric": f"{user_context.get('letters_generated', 0)}/2 lettres utilisées",
            "next_step": self._get_next_step_suggestion(user_context)
        }
    
    def _get_next_step_suggestion(self, user_context: Dict[str, Any]) -> str:
        """Suggère prochaine action optimale."""
        
        letters_generated = user_context.get("letters_generated", 0)
        has_cv = user_context.get("has_cv_uploaded", False)
        has_job_offer = user_context.get("has_job_offer", False)
        
        if letters_generated == 0:
            if not has_cv:
                return "Uploadez votre CV pour commencer"
            elif not has_job_offer:
                return "Ajoutez une offre d'emploi pour personnaliser"
            else:
                return "Générez votre première lettre maintenant"
        
        elif letters_generated == 1:
            return "Testez nos outils Premium sur votre lettre"
        
        elif letters_generated >= 2:
            return "Passez Premium pour lettres illimitées"
        
        return "Continuez votre reconversion"
    
    def track_engagement_event(
        self, 
        event_type: str, 
        user_id: str, 
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track événement d'engagement."""
        
        engagement_data = {
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "properties": properties or {}
        }
        
        self.logger.info(f"Engagement Event: {engagement_data}")
        
        # TODO: Sauvegarder en BDD pour analytics
        # TODO: Déclencher notifications push/email si configuré
    
    def get_retention_strategies(self, user_segment: str) -> List[Dict[str, Any]]:
        """Retourne stratégies de rétention par segment."""
        
        strategies = {
            "new_user": [
                {
                    "strategy": "guided_onboarding",
                    "description": "Tutoriel pas-à-pas première lettre",
                    "success_rate": 0.73
                },
                {
                    "strategy": "immediate_value",
                    "description": "Montrer résultat rapide avec suggestions",
                    "success_rate": 0.68
                }
            ],
            
            "limit_reached": [
                {
                    "strategy": "urgency_discount",
                    "description": "Offre limitée 24h après limite",
                    "success_rate": 0.31
                },
                {
                    "strategy": "feature_demonstration", 
                    "description": "Montrer valeur Premium avec démo",
                    "success_rate": 0.28
                }
            ],
            
            "active_free": [
                {
                    "strategy": "power_user_recognition",
                    "description": "Reconnaître expertise, proposer niveau Pro",
                    "success_rate": 0.45
                },
                {
                    "strategy": "exclusive_preview",
                    "description": "Accès anticipé nouvelles fonctionnalités",
                    "success_rate": 0.38
                }
            ]
        }
        
        return strategies.get(user_segment, [])