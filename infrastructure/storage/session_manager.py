"""Gestionnaire de session sécurisé et performant."""
import streamlit as st
import time
import logging
from typing import Any, Optional, Dict, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from config.settings import Settings
from shared.exceptions.specific_exceptions import SessionError, SecurityError

logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Données de session structurées."""
    user_id: str
    created_at: datetime
    last_activity: datetime
    data: Dict[str, Any]
    settings: Settings # Ajout de l'attribut settings
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si la session est expirée."""
        return (datetime.now() - self.last_activity).total_seconds() > self.settings.session_timeout
    
    @property
    def session_duration(self) -> float:
        """Durée de la session en secondes."""
        return (datetime.now() - self.created_at).total_seconds()

class SecureSessionManager:
    """Gestionnaire de session sécurisé avec validation et nettoyage automatique."""
    
    # Clés sensibles qui nécessitent un nettoyage spécial
    SENSITIVE_KEYS: Set[str] = {
        'cv_content', 'job_offer_content', 'generated_letter',
        'api_key', 'personal_data', 'uploaded_files'
    }
    
    # Clés critiques qui doivent persister
    CRITICAL_KEYS: Set[str] = {
        'user_id', 'session_id', 'user_tier', 'generation_count'
    }
    
    def __init__(self, settings: Settings):
        """Initialise le gestionnaire de session."""
        self.session_state = st.session_state
        self.settings = settings # Ajout de cette ligne pour stocker les settings
        self._init_session() # Initialise la session ici
        logger.info("SecureSessionManager initialized")
    
    def _init_session(self) -> None:
        """Initialise une nouvelle session ou récupère l'existante."""
        try:
            if 'session_data' not in st.session_state:
                # Check if a user_id is already set (e.g., by auth_middleware or guest access)
                user_id_to_use = st.session_state.get('user_id')
                if user_id_to_use is None:
                    user_id_to_use = self._generate_user_id()

                session_data = SessionData(
                    user_id=user_id_to_use,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    data={},
                    settings=self.settings # Passage de l'objet settings
                )
                st.session_state.session_data = session_data
                logger.info(f"New session created: {session_data.user_id}")
            else:
                # Mise à jour de l'activité
                st.session_state.session_data.last_activity = datetime.now()
                
                # Vérification d'expiration
                if st.session_state.session_data.is_expired:
                    logger.warning(f"Session expired: {st.session_state.session_data.user_id}")
                    self._cleanup_expired_session()
                    self._init_session()
                    
        except Exception as e:
            logger.error(f"Error initializing session: {e}")
            raise SessionError(f"Impossible d'initialiser la session: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de session.
        
        Args:
            key: Clé à récupérer
            default: Valeur par défaut
            
        Returns:
            Any: Valeur de session ou défaut
        """
        try:
            session_data: SessionData = st.session_state.session_data
            return session_data.data.get(key, default)
        except (KeyError, AttributeError):
            logger.warning(f"Session data not found for key: {key}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Définit une valeur de session avec validation.
        
        Args:
            key: Clé à définir
            value: Valeur à stocker
            
        Raises:
            SessionError: En cas d'erreur de stockage
            SecurityError: En cas de données sensibles non sécurisées
        """
        try:
            # Validation des données sensibles
            if key in self.SENSITIVE_KEYS:
                self._validate_sensitive_data(key, value)
            
            # Validation de la taille
            if isinstance(value, str) and len(value) > 100000:
                logger.warning(f"Large data stored in session for key: {key}")
            
            session_data: SessionData = st.session_state.session_data
            session_data.data[key] = value
            session_data.last_activity = datetime.now()
            
            logger.debug(f"Session value set for key: {key}")
            
        except Exception as e:
            logger.error(f"Error setting session value for key {key}: {e}")
            raise SessionError(f"Impossible de stocker la valeur: {e}")
    
    def delete(self, key: str) -> None:
        """
        Supprime une clé de session.
        
        Args:
            key: Clé à supprimer
        """
        try:
            session_data: SessionData = st.session_state.session_data
            if key in session_data.data:
                del session_data.data[key]
                logger.debug(f"Session key deleted: {key}")
        except Exception as e:
            logger.warning(f"Error deleting session key {key}: {e}")
    
    def clear_sensitive_data(self) -> None:
        """Nettoie toutes les données sensibles de la session."""
        try:
            session_data: SessionData = st.session_state.session_data
            for key in list(session_data.data.keys()):
                if key in self.SENSITIVE_KEYS:
                    del session_data.data[key]
            
            logger.info("Sensitive data cleared from session")
            
        except Exception as e:
            logger.error(f"Error clearing sensitive data: {e}")
    
    def reset_session(self) -> None:
        """Réinitialise complètement la session."""
        try:
            # Sauvegarde des données critiques
            critical_data = {}
            if 'session_data' in st.session_state:
                session_data: SessionData = st.session_state.session_data
                for key in self.CRITICAL_KEYS:
                    if key in session_data.data:
                        critical_data[key] = session_data.data[key]
            
            # Nettoyage complet
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Réinitialisation
            self._init_session()
            
            # Restauration des données critiques
            for key, value in critical_data.items():
                self.set(key, value)
            
            logger.info("Session reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            raise SessionError(f"Impossible de réinitialiser la session: {e}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Retourne les informations de session."""
        try:
            session_data: SessionData = st.session_state.session_data
            return {
                'user_id': session_data.user_id,
                'created_at': session_data.created_at.isoformat(),
                'last_activity': session_data.last_activity.isoformat(),
                'duration_seconds': session_data.session_duration,
                'data_keys': list(session_data.data.keys()),
                'data_size': len(str(session_data.data))
            }
        except Exception as e:
            logger.warning(f"Error getting session info: {e}")
            return {}
    
    def _generate_user_id(self) -> str:
        """Génère un ID utilisateur unique."""
        import secrets
        return f"user_{int(time.time())}_{secrets.token_hex(4)}"
    
    def _validate_sensitive_data(self, key: str, value: Any) -> None:
        """Valide les données sensibles avant stockage."""
        if key in {'api_key', 'personal_data'}:
            if not isinstance(value, str) or len(value) < 10:
                raise SecurityError(f"Invalid sensitive data for key: {key}")
        
        # Détection basique de données personnelles
        if isinstance(value, str):
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if re.search(email_pattern, value):
                logger.warning(f"Potential email detected in session data for key: {key}")
    
    def _cleanup_expired_session(self) -> None:
        """Nettoie une session expirée."""
        try:
            self.clear_sensitive_data()
            logger.info("Expired session cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up expired session: {e}")