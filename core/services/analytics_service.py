"""Service d'analytics pour tracking conversions et utilisation."""
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class AnalyticsEvent:
    """Événement analytics standardisé."""
    event_name: str
    user_id: str
    user_tier: str
    timestamp: datetime
    properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class AnalyticsService:
    """Service centralisé pour analytics et tracking conversions."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def track_event(
        self,
        event_name: str,
        user_id: str,
        user_tier: str = "free",
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Track un événement analytics.
        
        Args:
            event_name: Nom de l'événement (ex: "premium_cta_clicked")
            user_id: ID utilisateur
            user_tier: Tier utilisateur (free/premium)
            properties: Propriétés additionnelles
            session_id: ID de session
        """
        
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            user_tier=user_tier,
            timestamp=datetime.now(),
            properties=properties or {},
            session_id=session_id
        )
        
        # Log pour debugging et analytics locales
        self.logger.info(f"Analytics Event: {json.dumps(asdict(event), default=str)}")
        
        # TODO: Intégrer avec service analytics externe
        # self._send_to_analytics_service(event)
    
    def track_conversion_funnel(
        self,
        step: str,
        user_id: str,
        user_tier: str = "free",
        source: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track étapes du funnel de conversion.
        
        Args:
            step: Étape du funnel (page_view, cta_click, form_submit, payment)
            user_id: ID utilisateur
            user_tier: Tier utilisateur
            source: Source du trafic (popup, sidebar, page)
            properties: Propriétés additionnelles
        """
        
        funnel_properties = {
            "funnel_step": step,
            "source": source,
            **(properties or {})
        }
        
        self.track_event(
            event_name=f"conversion_funnel_{step}",
            user_id=user_id,
            user_tier=user_tier,
            properties=funnel_properties
        )
    
    def track_feature_usage(
        self,
        feature_name: str,
        user_id: str,
        user_tier: str,
        action: str = "used",
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track utilisation des fonctionnalités.
        
        Args:
            feature_name: Nom de la fonctionnalité (mirror_match, ats_analyzer, etc.)
            user_id: ID utilisateur
            user_tier: Tier utilisateur
            action: Action (used, blocked, upgraded)
            properties: Propriétés additionnelles
        """
        
        feature_properties = {
            "feature": feature_name,
            "action": action,
            **(properties or {})
        }
        
        self.track_event(
            event_name=f"feature_{action}",
            user_id=user_id,
            user_tier=user_tier,
            properties=feature_properties
        )
    
    def track_letter_generation(
        self,
        user_id: str,
        user_tier: str,
        generation_count: int,
        remaining_count: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track génération de lettres.
        
        Args:
            user_id: ID utilisateur
            user_tier: Tier utilisateur
            generation_count: Nombre total de lettres générées
            remaining_count: Lettres restantes pour Free users
            properties: Propriétés additionnelles
        """
        
        generation_properties = {
            "generation_count": generation_count,
            "remaining_count": remaining_count,
            **(properties or {})
        }
        
        self.track_event(
            event_name="letter_generated",
            user_id=user_id,
            user_tier=user_tier,
            properties=generation_properties
        )
    
    def get_conversion_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère métriques de conversion pour un utilisateur.
        
        Args:
            user_id: ID utilisateur
        Returns:
            Dict avec métriques de conversion
        """
        
        # TODO: Implémenter récupération depuis BDD/Analytics
        # Pour l'instant, retour mock data
        return {
            "total_events": 0,
            "conversion_events": 0,
            "last_activity": None,
            "funnel_completion": 0.0
        }
    
    def _send_to_analytics_service(self, event: AnalyticsEvent) -> None:
        """
        Envoie événement vers service analytics externe.
        
        Args:
            event: Événement à envoyer
        """
        
        # TODO: Intégrer avec Google Analytics, Mixpanel, etc.
        # Exemple implémentation:
        
        # Google Analytics 4
        # ga4_client.send_event(event.event_name, event.properties)
        
        # Mixpanel
        # mixpanel.track(event.user_id, event.event_name, event.properties)
        
        # Custom Analytics
        # requests.post("https://analytics.phoenixletters.com/events", json=asdict(event))
        
        pass