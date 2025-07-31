"""
Module contenant le service d'authentification et de gestion des utilisateurs.
Ce service est le cœur logique pour toutes les opérations liées aux utilisateurs.
"""
import bcrypt
from typing import Optional, Tuple

from core.entities.user import User
from infrastructure.auth.jwt_manager import JWTManager
from infrastructure.database.db_connection import DatabaseConnection
from shared.exceptions.specific_exceptions import UserNotFoundError, AuthenticationError, DatabaseError


class UserAuthService:
    """
    Gère la logique métier pour l'enregistrement, l'authentification et la gestion des utilisateurs.
    """

    def __init__(self, jwt_manager: JWTManager, db_connection: DatabaseConnection):
        self.jwt_manager = jwt_manager
        self.db = db_connection

    async def register_user(self, email: str, password: str, username: Optional[str] = None, newsletter_opt_in: bool = False) -> User:
        """Enregistre un nouvel utilisateur dans la base de données."""
        pool = self.db.get_pool()
        async with pool.acquire() as connection:
            # Vérifier si l'utilisateur existe déjà
            existing_user = await connection.fetchrow("SELECT * FROM users WHERE email = $1", email)
            if existing_user:
                raise AuthenticationError(f"L'utilisateur avec l'email {email} existe déjà.")

            # Hacher le mot de passe
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insérer le nouvel utilisateur
            try:
                new_user_record = await connection.fetchrow(
                    """INSERT INTO users (email, password_hash, username, newsletter_opt_in) 
                       VALUES ($1, $2, $3, $4) 
                       RETURNING id, email, username, created_at, status, newsletter_opt_in""",
                    email, hashed_password, username, newsletter_opt_in
                )
                # Créer et retourner l'entité User
                return User(id=new_user_record['id'], email=new_user_record['email'], username=new_user_record['username'], newsletter_opt_in=new_user_record['newsletter_opt_in'])
            except Exception as e:
                raise DatabaseError(f"Erreur lors de la création de l'utilisateur: {e}")

    async def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        """Authentifie un utilisateur et retourne l'utilisateur avec les tokens d'accès et de rafraîchissement."""
        pool = self.db.get_pool()
        async with pool.acquire() as connection:
            user_record = await connection.fetchrow("SELECT u.*, s.current_tier FROM users u LEFT JOIN user_subscriptions s ON u.id = s.user_id WHERE u.email = $1", email)

            if not user_record:
                raise UserNotFoundError(f"Aucun utilisateur trouvé avec l'email {email}.")

            if not bcrypt.checkpw(password.encode('utf-8'), user_record['password_hash'].encode('utf-8')):
                raise AuthenticationError("Mot de passe incorrect.")

            user_tier = user_record['current_tier'] if user_record['current_tier'] else UserTier.FREE.value
            user = User(
                id=user_record['id'],
                email=user_record['email'],
                username=user_record['username'],
                email_verified=user_record['email_verified'],
                newsletter_opt_in=user_record['newsletter_opt_in'],
                status=user_record['status'],
                created_at=user_record['created_at'],
                subscription=UserSubscription(current_tier=UserTier(user_tier))
            )
            
            # Générer les tokens
            access_token = self.jwt_manager.create_access_token(user=user)
            refresh_token = self.jwt_manager.create_refresh_token(user=user)

            return user, access_token, refresh_token

    def verify_email(self, token: str) -> bool:
        """Vérifie l'email de l'utilisateur à l'aide d'un token."""
        pass

    def reset_password(self, email: str) -> str:
        """Génère et envoie un token de réinitialisation de mot de passe."""
        # Retour attendu : token
        pass

    def change_password(self, user_id: int, old_pass: str, new_pass: str) -> bool:
        """Change le mot de passe d'un utilisateur authentifié."""
        pass

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        pool = self.db.get_pool()
        async with pool.acquire() as connection:
            user_record = await connection.fetchrow("SELECT u.*, s.current_tier FROM users u LEFT JOIN user_subscriptions s ON u.id = s.user_id WHERE u.id = $1", user_id)
            if user_record:
                user_tier = user_record['current_tier'] if user_record['current_tier'] else UserTier.FREE.value
                return User(
                    id=user_record['id'],
                    email=user_record['email'],
                    username=user_record['username'],
                    email_verified=user_record['email_verified'],
                    newsletter_opt_in=user_record['newsletter_opt_in'],
                    status=user_record['status'],
                    created_at=user_record['created_at'],
                    subscription=UserSubscription(current_tier=UserTier(user_tier))
                )
            return None

    def update_user_profile(self, user_id: int, profile_data: dict) -> 'User':
        """Met à jour le profil d'un utilisateur."""
        pass

    def deactivate_user(self, user_id: int) -> bool:
        """Désactive le compte d'un utilisateur."""
        pass
