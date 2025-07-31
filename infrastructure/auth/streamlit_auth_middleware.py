"""
Module pour le middleware d'authentification Streamlit.
Contient les décorateurs et les fonctions pour gérer l'accès aux pages
et l'affichage des composants d'interface utilisateur liés à l'authentification.
"""
import streamlit as st
from typing import Optional

from core.entities.user import User
from infrastructure.auth.user_auth_service import UserAuthService
from infrastructure.auth.jwt_manager import JWTManager

class StreamlitAuthMiddleware:
    """
    Gère l'authentification et le contrôle d'accès pour l'interface Streamlit.
    """

    def __init__(self, auth_service: UserAuthService, jwt_manager: JWTManager):
        self.auth_service = auth_service
        self.jwt_manager = jwt_manager

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
            return self.auth_service.get_user_by_id(user_id)
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
                        user, access_token, refresh_token = self.auth_service.authenticate_user(email, password)
                        st.session_state['auth_token'] = access_token
                        st.session_state['refresh_token'] = refresh_token
                        st.session_state['user_id'] = str(user.id)
                        st.session_state['user_tier'] = user.subscription.current_tier
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
                        user = self.auth_service.register_user(email, password, username, newsletter_opt_in)
                        st.success(f"Compte créé pour {user.email} ! Vous pouvez maintenant vous connecter.")
                        # Après l'inscription, on peut rediriger vers l'onglet de connexion ou laisser l'utilisateur se connecter
                        # Pour l'instant, on ne connecte pas automatiquement après l'inscription.
                        st.rerun()
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
