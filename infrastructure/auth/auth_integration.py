"""Module d'intégration progressive du système d'authentification avec l'architecture existante."""
import logging
import streamlit as st
from typing import Optional
from datetime import datetime

from config.settings import Settings
from infrastructure.auth.user_auth_service import UserAuthService
from infrastructure.auth.jwt_manager import JWTManager
from infrastructure.auth.streamlit_auth_middleware import StreamlitAuthMiddleware
from core.entities.user import User, UserTier
from core.entities.letter import UserTier as LegacyUserTier

logger = logging.getLogger(__name__)


class AuthIntegration:
    """
    Classe d'intégration pour transition progressive vers le système d'authentification.
    Permet la coexistence entre l'ancien système (session_state) et le nouveau (DB + JWT).
    """
    
    def __init__(self, settings: Settings):
        """
        Initialise l'intégration auth.
        
        Args:
            settings: Configuration de l'application
        """
        self.settings = settings
        
        # Initialisation composants auth (en mode stub pour l'instant)
        self.jwt_manager = JWTManager(settings)
        self.auth_service = UserAuthService(settings, self.jwt_manager)
        self.auth_middleware = StreamlitAuthMiddleware(settings, self.auth_service, self.jwt_manager)
        
        # Mode d'activation progressive
        self.auth_enabled = settings.enable_authentication if hasattr(settings, 'enable_authentication') else False
        
        logger.info(f"AuthIntegration initialized - Auth enabled: {self.auth_enabled}")
    
    def get_user_tier(self) -> UserTier:
        """
        Récupère le tier utilisateur selon le mode actif.
        
        Returns:
            UserTier: Tier de l'utilisateur
        """
        if self.auth_enabled:
            # Mode authentification : récupération depuis utilisateur connecté
            current_user = self.auth_middleware.get_current_user()
            if current_user:
                return current_user.subscription.current_tier
            return UserTier.FREE
        else:
            # Mode legacy : récupération depuis session_state
            legacy_tier = st.session_state.get('user_tier', LegacyUserTier.FREE)
            return self._convert_legacy_tier(legacy_tier)
    
    def get_current_user(self) -> Optional[User]:
        """
        Récupère l'utilisateur actuel si authentification activée.
        
        Returns:
            Optional[User]: Utilisateur connecté ou None
        """
        if self.auth_enabled:
            return self.auth_middleware.get_current_user()
        return None
    
    def get_user_id(self) -> str:
        """
        Récupère l'ID utilisateur selon le mode actif.
        
        Returns:
            str: ID utilisateur
        """
        if self.auth_enabled:
            current_user = self.auth_middleware.get_current_user()
            if current_user:
                return str(current_user.id)
            return "anonymous"
        else:
            # Mode legacy : utilisation du user_id de session
            from infrastructure.storage.session_manager import SecureSessionManager
            session_info = st.session_state.get('session_data')
            if session_info and hasattr(session_info, 'user_id'):
                return session_info.user_id
            return "anonymous"
    
    def is_authenticated(self) -> bool:
        """
        Vérifie si l'utilisateur est authentifié.
        
        Returns:
            bool: True si authentifié (ou mode legacy)
        """
        if self.auth_enabled:
            return self.auth_middleware.get_current_user() is not None
        else:
            # Mode legacy : toujours considéré comme "authentifié"
            return True
    
    def require_authentication(self) -> bool:
        """
        Force l'authentification si le mode auth est activé.
        
        Returns:
            bool: True si authentifié ou mode legacy
        """
        if not self.auth_enabled:
            return True
        
        current_user = self.auth_middleware.get_current_user()
        if not current_user:
            st.warning("🔐 **Authentification requise**")
            st.info("Vous devez vous connecter pour utiliser Phoenix Letters.")
            
            # Affichage formulaire de connexion
            self.auth_middleware.render_login_form()
            return False
        
        return True
    
    def require_tier(self, required_tier: UserTier) -> bool:
        """
        Vérifie si l'utilisateur a le tier requis.
        
        Args:
            required_tier: Tier minimum requis
            
        Returns:
            bool: True si tier suffisant
        """
        user_tier = self.get_user_tier()
        
        if not self._has_required_tier(user_tier, required_tier):
            st.error(f"💎 **Abonnement {required_tier.value.title()} requis**")
            st.info("Cette fonctionnalité nécessite un abonnement Premium.")
            
            if not self.auth_enabled:
                st.info("💡 **Mode Bêta-Testeur**: Activez le mode Bêta-Testeur dans la sidebar pour débloquer toutes les fonctionnalités.")
            else:
                if st.button("🚀 Passer à Premium", key="upgrade_btn"):
                    st.session_state["show_upgrade_modal"] = True
                    st.rerun()
            
            return False
        
        return True
    
    def render_user_section(self) -> None:
        """Affiche la section utilisateur dans la sidebar."""
        if self.auth_enabled:
            # Mode authentification : informations utilisateur complètes
            self.auth_middleware.render_user_info()
        else:
            # Mode legacy : informations basiques depuis session
            self._render_legacy_user_info()
    
    def get_generation_limit_info(self) -> dict:
        """
        Récupère les informations de limite de génération.
        
        Returns:
            dict: Informations sur les limites
        """
        user_tier = self.get_user_tier()
        
        if user_tier == UserTier.FREE:
            # En mode legacy, utiliser les données de session
            if not self.auth_enabled:
                generation_count = st.session_state.get('free_generations_count', 0)
                return {
                    'current': generation_count,
                    'limit': 5,  # Limite FREE
                    'remaining': max(0, 5 - generation_count)
                }
            else:
                # Mode auth : utiliser les stats utilisateur
                current_user = self.auth_middleware.get_current_user()
                if current_user:
                    stats = current_user.usage_stats
                    return {
                        'current': stats.letters_generated_this_month,
                        'limit': 5,
                        'remaining': max(0, 5 - stats.letters_generated_this_month)
                    }
        
        # Premium : pas de limite
        return {
            'current': 0,
            'limit': -1,  # Illimité
            'remaining': -1
        }
    
    def increment_generation_count(self) -> None:
        """Incrémente le compteur de génération selon le mode."""
        user_tier = self.get_user_tier()
        
        if user_tier == UserTier.FREE:
            if not self.auth_enabled:
                # Mode legacy : incrémenter session_state
                current_count = st.session_state.get('free_generations_count', 0)
                st.session_state.free_generations_count = current_count + 1
            else:
                # Mode auth : incrémenter stats utilisateur
                current_user = self.auth_middleware.get_current_user()
                if current_user:
                    current_user.usage_stats.increment_generation()
                    # TODO: Sauvegarder en DB
    
    # Méthodes privées
    
    def _convert_legacy_tier(self, legacy_tier: LegacyUserTier) -> UserTier:
        """Convertit un tier legacy vers le nouveau système."""
        conversion_map = {
            LegacyUserTier.FREE: UserTier.FREE,
            LegacyUserTier.PREMIUM: UserTier.PREMIUM,
            LegacyUserTier.PREMIUM_PLUS: UserTier.PREMIUM_PLUS
        }
        return conversion_map.get(legacy_tier, UserTier.FREE)
    
    def _has_required_tier(self, user_tier: UserTier, required_tier: UserTier) -> bool:
        """Vérifie si l'utilisateur a le tier requis."""
        tier_hierarchy = {
            UserTier.FREE: 0,
            UserTier.PREMIUM: 1,
            UserTier.PREMIUM_PLUS: 2
        }
        
        return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)
    
    def _render_legacy_user_info(self) -> None:
        """Affiche les informations utilisateur en mode legacy."""
        with st.sidebar:
            st.write("**👤 Mode Session**")
            
            user_tier = self.get_user_tier()
            st.write(f"🎫 {user_tier.value.title()}")
            
            # Compteur de génération pour FREE
            if user_tier == UserTier.FREE:
                limit_info = self.get_generation_limit_info()
                st.write(f"📝 Lettres générées: {limit_info['current']}/{limit_info['limit']}")
                
                # Barre de progression
                if limit_info['limit'] > 0:
                    progress = limit_info['current'] / limit_info['limit']
                    st.progress(min(progress, 1.0))
            
            # Mode bêta-testeur actuel
            is_beta = st.session_state.get('user_tier') == LegacyUserTier.PREMIUM_PLUS
            if is_beta:
                st.success("🧪 Mode Bêta-Testeur actif")
    
    def setup_navigation_auth_check(self) -> bool:
        """
        Vérifie l'authentification pour la navigation.
        À appeler en début d'app.py.
        
        Returns:
            bool: True si l'utilisateur peut continuer
        """
        if not self.auth_enabled:
            return True
        
        # Vérification session valide
        if not self.auth_middleware.check_session_validity():
            st.warning("🔐 Votre session a expiré. Veuillez vous reconnecter.")
            self.auth_middleware.render_login_form()
            return False
        
        return True