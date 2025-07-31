"""
Module contenant le service d'authentification et de gestion des utilisateurs.
Ce service est le cœur logique pour toutes les opérations liées aux utilisateurs.
"""
import bcrypt
from typing import Optional, Tuple
from datetime import datetime
import uuid
import traceback

from core.entities.user import User, UserTier, UserSubscription
from infrastructure.auth.jwt_manager import JWTManager
from infrastructure.database.db_connection import DatabaseConnection
from shared.exceptions.specific_exceptions import UserNotFoundError, AuthenticationError, DatabaseError


class UserAuthService:
    """
    Gère la logique métier pour l'enregistrement, l'authentification et la gestion des utilisateurs.
    """

    def __init__(self, jwt_manager: JWTManager, db_connection: DatabaseConnection):
        self.jwt_manager = jwt_manager
        self.client = db_connection.get_client()

    def register_user(self, email: str, password: str, username: Optional[str] = None, newsletter_opt_in: bool = False) -> User:
        """Enregistre un nouvel utilisateur dans la base de données."""
        # Vérifier si l'utilisateur existe déjà
        response = self.client.from_('users').select("id").eq("email", email).execute()
        if response.data:
            raise AuthenticationError(f"L'utilisateur avec l'email {email} existe déjà.")

        # Hacher le mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insérer le nouvel utilisateur
        try:
            user_data = {
                'email': email,
                'password_hash': hashed_password,
                'username': username,
                'newsletter_opt_in': newsletter_opt_in
            }
            response = self.client.from_('users').insert(user_data).execute()
            
            if not response.data:
                raise DatabaseError("La création de l'utilisateur a échoué, aucune donnée retournée.")

            new_user_record = response.data[0]
            # Créer et retourner l'entité User
            return User(id=new_user_record['id'], email=new_user_record['email'], username=new_user_record['username'], newsletter_opt_in=new_user_record['newsletter_opt_in'])
        except Exception as e:
            raise DatabaseError(f"Erreur lors de la création de l'utilisateur: {e}")

    def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        """Authentifie un utilisateur et retourne l'utilisateur avec les tokens d'accès et de rafraîchissement."""
        response = self.client.from_('users').select("*, user_subscriptions(current_tier)").eq("email", email).execute()

        if not response.data:
            raise UserNotFoundError(f"Aucun utilisateur trouvé avec l'email {email}.")

        user_record = response.data[0]

        # Gestion de l'abonnement
        subscription_data = user_record.get('user_subscriptions')
        # Vérification robuste : la liste doit exister ET ne pas être vide
        if subscription_data and isinstance(subscription_data, list) and subscription_data:
            user_tier = UserTier(subscription_data[0]['current_tier'])
        else:
            user_tier = UserTier.FREE
        subscription = UserSubscription(current_tier=user_tier)

        if not bcrypt.checkpw(password.encode('utf-8'), user_record['password_hash'].encode('utf-8')):
            raise AuthenticationError("Mot de passe incorrect.")

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

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        response = self.client.from_('users').select("*, user_subscriptions(current_tier)").eq("id", user_id).execute()
        if response.data:
            user_record = response.data[0]
            
            # Gestion de l'abonnement
            subscription_data = user_record.get('user_subscriptions')
            # Vérification robuste : la liste doit exister ET ne pas être vide
            if subscription_data and isinstance(subscription_data, list) and subscription_data:
                user_tier = UserTier(subscription_data[0]['current_tier'])
            else:
                user_tier = UserTier.FREE
            subscription = UserSubscription(current_tier=user_tier)

            return User(
                id=uuid.UUID(user_record['id']),
                email=user_record['email'],
                username=user_record.get('username'),
                status=user_record.get('status', 'pending'),
                email_verified=user_record.get('email_verified', False),
                newsletter_opt_in=user_record.get('newsletter_opt_in', False),
                created_at=datetime.fromisoformat(user_record['created_at']),
                subscription=subscription
            )
        return None

    def update_user_profile(self, user_id: int, profile_data: dict) -> 'User':
        """Met à jour le profil d'un utilisateur."""
        pass

    def deactivate_user(self, user_id: int) -> bool:
        """Désactive le compte d'un utilisateur."""
        pass
