"""
Module pour le middleware d'authentification Streamlit.
Contient les décorateurs et les fonctions pour gérer l'accès aux pages
et l'affichage des composants d'interface utilisateur liés à l'authentification.
"""
import streamlit as st
import asyncio
from typing import Optional, Callable

from core.entities.user import User, UserTier
from infrastructure.auth.user_auth_service import UserAuthService
from infrastructure.auth.jwt_manager import JWTManager
from utils.async_runner import AsyncServiceRunner # Import du runner

class StreamlitAuthMiddleware:
    """
    Gère l'authentification et le contrôle d'accès pour l'interface Streamlit.
    """

    def __init__(self, auth_service: UserAuthService, jwt_manager: JWTManager):
        self.auth_service = auth_service
        self.jwt_manager = jwt_manager
        self.async_runner: AsyncServiceRunner = st.session_state.async_service_runner

    def _run_async(self, coro):
        """Exécute une coroutine asynchrone dans le contexte de Streamlit."""
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(coro)
        except RuntimeError: # Pas de boucle d'événements en cours d'exécution
            return asyncio.run(coro)

    def get_current_user(self) -> Optional[User]:
        """Récupère l'utilisateur actuellement connecté depuis le token JWT stocké dans les cookies."""
        if 'auth_token' not in st.session_state:
            return None

        token = st.session_state['auth_token']
        payload = self.jwt_manager.decode_token(token)

        if not payload or payload['type'] != 'access':
            return None

        user_id = payload.get('sub')
        if not user_id:
            return None

        try:
            return self.async_runner.run_coro_in_thread(self.auth_service.get_user_by_id(user_id)).result()
        except Exception as e:
            st.error(f"Erreur de session: {e}")
            return None

    def login_form(self) -> Optional[User]:
        """Affiche un formulaire de connexion/inscription et gère la soumission."""
        st.subheader("Connectez-vous ou créez un compte")

        login_tab, register_tab = st.tabs(["Connexion", "Inscription"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mot de passe", type="password", key="login_password")
                submitted = st.form_submit_button("Se connecter")

                if submitted:
                    try:
                        user, access_token, refresh_token = self.async_runner.run_coro_in_thread(self.auth_service.authenticate_user(email, password)).result()
                        st.session_state['auth_token'] = access_token
                        st.session_state['refresh_token'] = refresh_token
                        st.session_state['user_id'] = str(user.id) # Mettre à jour user_id dans session_state
                        st.session_state['user_tier'] = user.subscription.current_tier # Mettre à jour user_tier
                        st.success("Connexion réussie !")
                        st.rerun()
                        return user
                    except Exception as e:
                        st.error(f"Email ou mot de passe incorrect: {e}")
                        return None

        with register_tab:
            with st.form("register_form"):
                email = st.text_input("Email", key="register_email")
                username = st.text_input("Nom d'utilisateur (optionnel)", key="register_username")
                password = st.text_input("Mot de passe", type="password", key="register_password")
                newsletter_opt_in = st.checkbox("Je souhaite recevoir la newsletter Phoenix Letters", value=False, key="register_newsletter_opt_in")
                submitted = st.form_submit_button("S'inscrire")

                if submitted:
                    try:
                        user = self.async_runner.run_coro_in_thread(self.auth_service.register_user(email, password, username, newsletter_opt_in)).result()
                        st.success(f"Compte créé pour {user.email} ! Vous pouvez maintenant vous connecter.")
                        # Après l'inscription, on peut rediriger vers l'onglet de connexion ou laisser l'utilisateur se connecter
                        # Pour l'instant, on ne connecte pas automatiquement après l'inscription.
                        st.rerun()
                        return None # Ne retourne pas l'utilisateur car il n'est pas encore connecté
                    except Exception as e:
                        st.error(f"Erreur lors de l'inscription: {e}")
                        return None
        return None

    def logout(self) -> None:
        """Déconnecte l'utilisateur et nettoie la session."""
        if 'auth_token' in st.session_state:
            del st.session_state['auth_token']
        if 'refresh_token' in st.session_state:
            del st.session_state['refresh_token']
        st.success("Vous avez été déconnecté.")

    def check_session_validity(self) -> bool:
        """Vérifie si la session de l'utilisateur est toujours valide."""
        pass
