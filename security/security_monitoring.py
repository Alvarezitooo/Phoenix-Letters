"""Monitoring sécurité temps réel pour Phoenix Letters."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass 
class SecurityEvent:
    """Événement de sécurité."""
    timestamp: datetime
    severity: str  # "info", "warning", "critical"
    category: str  # "auth_failure", "injection_attempt", "rate_limit_exceeded"
    source_ip: str
    user_id: Optional[str]
    details: Dict[str, Any]
    action_taken: str


class SecurityMonitor:
    """Moniteur de sécurité temps réel."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.events: List[SecurityEvent] = []
        self.alert_thresholds = {
            "failed_logins": 5,
            "injection_attempts": 1,
            "suspicious_patterns": 3
        }
    
    def log_security_event(self, event: SecurityEvent) -> None:
        """Log événement sécurité."""
        self.events.append(event)
        self.logger.warning(f"Security Event: {event.category} - {event.severity}")
        
        # Déclencher alertes si nécessaire
        if event.severity == "critical":
            self._trigger_alert(event)
    
    def _trigger_alert(self, event: SecurityEvent) -> None:
        """Déclenche alerte sécurité."""
        self.logger.critical(f"SECURITY ALERT: {event.category} from {event.source_ip}")
        # TODO: Intégrer avec système alertes (email, Slack, etc.)
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Retourne dashboard sécurité."""
        recent_events = [e for e in self.events if e.timestamp > datetime.now() - timedelta(hours=24)]
        
        return {
            "total_events_24h": len(recent_events),
            "critical_events": len([e for e in recent_events if e.severity == "critical"]),
            "top_attack_categories": self._get_top_categories(recent_events),
            "suspicious_ips": self._get_suspicious_ips(recent_events)
        }
    
    def _get_top_categories(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Retourne top catégories d'attaques."""
        categories = {}
        for event in events:
            categories[event.category] = categories.get(event.category, 0) + 1
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5])
    
    def _get_suspicious_ips(self, events: List[SecurityEvent]) -> List[str]:
        """Retourne IPs suspectes."""
        ip_counts = {}
        for event in events:
            if event.severity in ["warning", "critical"]:
                ip_counts[event.source_ip] = ip_counts.get(event.source_ip, 0) + 1
        
        return [ip for ip, count in ip_counts.items() if count >= 3]