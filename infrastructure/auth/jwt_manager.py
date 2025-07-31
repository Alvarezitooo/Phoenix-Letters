"""
Gestionnaire de tokens JWT pour Phoenix Letters.
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional

from core.entities.user import User
from config.settings import Settings

class JWTManager:
    """
    Gère la création, l'encodage et le décodage des tokens JWT.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def _create_token(self, user: User, expires_delta: timedelta, token_type: str) -> str:
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow(),
            "type": token_type
        }
        return jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm="HS256")

    def create_access_token(self, user: User) -> str:
        """Crée un token d'accès JWT."""
        expires_delta = timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        return self._create_token(user, expires_delta, "access")

    def create_refresh_token(self, user: User) -> str:
        """Crée un token de rafraîchissement JWT."""
        expires_delta = timedelta(days=self.settings.jwt_refresh_token_expire_days)
        return self._create_token(user, expires_delta, "refresh")

    def decode_token(self, token: str) -> Optional[dict]:
        """Décode un token JWT et retourne son payload."""
        try:
            payload = jwt.decode(token, self.settings.jwt_secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None
