"""Gestionnaire thread-safe des limites utilisateur."""
import logging
import threading
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

from core.entities.letter import UserTier
from shared.exceptions.specific_exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class UserLimitState:
    """État des limites pour un utilisateur."""
    free_generations_count: int = 0
    last_generation_month: Optional[int] = None
    

class UserLimitManager:
    """Gestionnaire thread-safe des limites utilisateur."""
    
    # Configuration
    FREE_MONTHLY_LIMIT = 2
    
    def __init__(self, session_manager):
        """
        Initialise le gestionnaire de limites.
        
        Args:
            session_manager: Gestionnaire de session Streamlit
        """
        self._session_manager = session_manager
        self._lock = threading.RLock()  # Réentrant lock pour sécurité
        logger.info("UserLimitManager initialized")
    
    @contextmanager
    def _thread_safe_session(self):
        """Context manager pour accès thread-safe à la session."""
        with self._lock:
            try:
                yield self._session_manager
            except Exception as e:
                logger.error(f"Session access error: {e}")
                raise
    
    def _get_current_limit_state(self) -> UserLimitState:
        """Récupère l'état actuel des limites de manière thread-safe."""
        with self._thread_safe_session() as session:
            return UserLimitState(
                free_generations_count=session.get('free_generations_count', 0),
                last_generation_month=session.get('last_free_generation_month')
            )
    
    def _update_limit_state(self, state: UserLimitState) -> None:
        """Met à jour l'état des limites de manière atomique."""
        with self._thread_safe_session() as session:
            session.set('free_generations_count', state.free_generations_count)
            session.set('last_free_generation_month', state.last_generation_month)
    
    def _reset_monthly_counter(self, current_month: int) -> UserLimitState:
        """Remet à zéro le compteur mensuel."""
        new_state = UserLimitState(
            free_generations_count=0,
            last_generation_month=current_month
        )
        self._update_limit_state(new_state)
        logger.info(f"Monthly counter reset for month {current_month}")
        return new_state
    
    def check_generation_limit(self, user_tier: UserTier, user_id: str) -> None:
        """
        Vérifie si l'utilisateur peut générer une lettre.
        
        Args:
            user_tier: Niveau d'abonnement de l'utilisateur
            user_id: Identifiant de l'utilisateur (pour logs)
            
        Raises:
            ValidationError: Si la limite est atteinte
        """
        # Les utilisateurs Premium n'ont pas de limite
        if user_tier != UserTier.FREE:
            return
        
        current_month = datetime.now().month
        
        # Accès atomique à l'état
        with self._lock:
            current_state = self._get_current_limit_state()
            
            # Vérification si nouveau mois
            if current_state.last_generation_month != current_month:
                current_state = self._reset_monthly_counter(current_month)
            
            # Vérification de la limite
            if current_state.free_generations_count >= self.FREE_MONTHLY_LIMIT:
                logger.warning(
                    f"Generation limit reached for FREE user {user_id}",
                    extra={
                        "user_id": user_id,
                        "current_count": current_state.free_generations_count,
                        "limit": self.FREE_MONTHLY_LIMIT,
                        "month": current_month
                    }
                )
                raise ValidationError(
                    f"Les utilisateurs Free sont limités à {self.FREE_MONTHLY_LIMIT} lettres "
                    f"générées par mois. Passez Premium pour une génération illimitée."
                )
        
        logger.debug(
            f"Generation limit check passed for user {user_id}",
            extra={
                "user_tier": user_tier.value,
                "current_count": current_state.free_generations_count,
                "limit": self.FREE_MONTHLY_LIMIT
            }
        )
    
    def increment_generation_count(self, user_tier: UserTier, user_id: str) -> None:
        """
        Incrémente le compteur de génération après succès.
        
        Args:
            user_tier: Niveau d'abonnement de l'utilisateur
            user_id: Identifiant de l'utilisateur (pour logs)
        """
        # Seuls les utilisateurs FREE sont comptabilisés
        if user_tier != UserTier.FREE:
            return
        
        current_month = datetime.now().month
        
        # Mise à jour atomique
        with self._lock:
            current_state = self._get_current_limit_state()
            
            # Sécurité : vérifier que le mois est cohérent
            if current_state.last_generation_month != current_month:
                current_state = self._reset_monthly_counter(current_month)
            
            # Incrément sécurisé
            current_state.free_generations_count += 1
            current_state.last_generation_month = current_month
            
            self._update_limit_state(current_state)
        
        logger.info(
            f"Generation count incremented for user {user_id}",
            extra={
                "user_id": user_id,
                "new_count": current_state.free_generations_count,
                "limit": self.FREE_MONTHLY_LIMIT,
                "month": current_month
            }
        )
    
    def get_remaining_generations(self, user_tier: UserTier) -> Optional[int]:
        """
        Retourne le nombre de générations restantes pour les utilisateurs FREE.
        
        Args:
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            Optional[int]: Nombre de générations restantes (None pour Premium)
        """
        if user_tier != UserTier.FREE:
            return None  # Illimité pour Premium
        
        current_month = datetime.now().month
        
        with self._lock:
            current_state = self._get_current_limit_state()
            
            # Si nouveau mois, tout est disponible
            if current_state.last_generation_month != current_month:
                return self.FREE_MONTHLY_LIMIT
            
            # Calcul des générations restantes
            remaining = max(0, self.FREE_MONTHLY_LIMIT - current_state.free_generations_count)
            return remaining