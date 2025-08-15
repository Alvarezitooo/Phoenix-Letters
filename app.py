import streamlit as st
import logging
import asyncio
import sys
import os
from datetime import datetime

# Ajout du chemin vers phoenix_shared pour l'import SSO
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../phoenix_shared'))

from config.settings import Settings
from infrastructure.storage.session_manager import SecureSessionManager
from infrastructure.security.input_validator import InputValidator
from core.services.prompt_service import PromptService
from infrastructure.ai.gemini_client import GeminiClient
from infrastructure.monitoring.performance_monitor import PerformanceMonitor
from core.services.letter_service import LetterService
from core.services.job_offer_parser import JobOfferParser
from ui.components.file_uploader import SecureFileUploader
from ui.components.progress_bar import ProgressIndicator
from ui.components.letter_editor import LetterEditor
from ui.pages.generator_page import GeneratorPage
from ui.pages.about_page import AboutPage
from ui.pages.premium_page import PremiumPage
from ui.pages.settings_page import SettingsPage
from utils.monitoring import APIUsageTracker, render_api_monitoring_dashboard, render_detailed_monitoring, diagnostic_urgence_50_requetes
from utils.async_runner import AsyncServiceRunner

from core.entities.user import UserTier
from infrastructure.auth.jwt_manager import JWTManager
from infrastructure.auth.user_auth_service import UserAuthService
from infrastructure.auth.streamlit_auth_middleware import StreamlitAuthMiddleware
from infrastructure.database.db_connection import DatabaseConnection

# Import du système SSO Phoenix
from auth.phoenix_sso import phoenix_sso, render_phoenix_navigation, show_phoenix_user_badge

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Fonctions de Rendu des Pages ---

def render_choice_page():
    """Affiche la page de choix initial (Invité ou Connexion)."""
    st.title("🔥 Phoenix Letters")
    st.write("Bienvenue sur Phoenix Letters, votre assistant pour des lettres de motivation percutantes.")
    st.write("Choisissez comment vous souhaitez commencer :")

    col1, col2 = st.columns(2)
    if col1.button("🚀 Commencer ma lettre (gratuit)", use_container_width=True, key="guest_access_button"):
        st.session_state.auth_flow_choice = 'guest'
        st.session_state.guest_user_id = f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.session_state.user_tier = UserTier.FREE
        st.rerun()
    if col2.button("🔑 Se connecter / S'inscrire", use_container_width=True, key="login_register_button"):
        st.session_state.auth_flow_choice = 'login'
        st.rerun()

def render_login_page(auth_middleware):
    """Affiche le formulaire de connexion/inscription."""
    st.title("🔥 Phoenix Letters - Connexion / Inscription")
    auth_middleware.login_form()

def render_main_app(current_user, auth_middleware, settings, phoenix_mode=False):
    """Affiche l'application principale une fois l'utilisateur authentifié ou en mode invité."""
    
    if phoenix_mode and current_user:
        # Mode SSO Phoenix - Interface modernisée
        user_name = current_user.get('full_name') or current_user.get('email', 'Phoenix User')
        user_tier = current_user.get('user_tier', 'free').title()
        
        st.title(f"🔥 Phoenix Letters - {user_name}")
        st.markdown(f"**🏆 Tier Phoenix: {user_tier}**")
        
        # Bouton déconnexion Phoenix dans sidebar
        with st.sidebar:
            if st.button("🚪 Déconnexion Phoenix", type="secondary"):
                phoenix_sso.logout()
                st.rerun()
                
    elif current_user and not phoenix_mode:
        # Mode authentification classique
        st.title(f"🔥 Phoenix Letters - Bienvenue, {current_user.email}")
        if st.sidebar.button("Se déconnecter"):
            auth_middleware.logout()
            st.rerun()
    else: 
        # Mode invité
        st.title("🔥 Phoenix Letters - Mode Invité")
        st.sidebar.info(
            "🚀 **Débloquez tout le potentiel de Phoenix Letters !**\n\n"
            "En créant un compte gratuit, vous pourrez :\n"
            "- **Sauvegarder** et retrouver toutes vos lettres\n"
            "- Accéder à l'**historique** de vos générations\n"
            "- Bénéficier de **fonctionnalités Premium** exclusives (bientôt !)\n"
            "- Recevoir des **conseils personnalisés** pour votre carrière\n\n"
            "**N'attendez plus, inscrivez-vous !**"
        )
        if 'user_id' not in st.session_state:
            st.session_state.user_id = st.session_state.get('guest_user_id', 'guest_fallback')
        if 'user_tier' not in st.session_state:
            st.session_state.user_tier = UserTier.FREE

    # --- AIGUILLAGE API (INTERRUPTEUR) ---
    use_mock = st.sidebar.checkbox("Utiliser le Mock API (Mode Développeur)", value=True)
    if use_mock:
        from infrastructure.ai.mock_gemini_client import MockGeminiClient
        gemini_client = MockGeminiClient()
        st.sidebar.warning("Mode Mock API activé.")
    else:
        gemini_client = GeminiClient(settings)
        st.sidebar.success("Mode API Réelle activé.")
    
    # Initialisation des services et composants UI
    session_manager = SecureSessionManager(settings)
    input_validator = InputValidator()
    prompt_service = PromptService(settings)
    from core.services.mirror_match_service import MirrorMatchService
    from core.services.ats_analyzer_service import ATSAnalyzerService
    from core.services.smart_coach_service import SmartCoachService
    from core.services.trajectory_builder_service import TrajectoryBuilderService

    mirror_match_service = MirrorMatchService(gemini_client, input_validator)
    ats_analyzer_service = ATSAnalyzerService(gemini_client, input_validator)
    smart_coach_service = SmartCoachService(gemini_client, input_validator)
    trajectory_builder_service = TrajectoryBuilderService(gemini_client, input_validator)
    letter_service = LetterService(gemini_client, input_validator, prompt_service, session_manager)
    job_offer_parser = JobOfferParser()
    file_uploader = SecureFileUploader(input_validator, settings)
    progress_indicator = ProgressIndicator()
    letter_editor = LetterEditor()

    generator_page = GeneratorPage(
        letter_service=letter_service,
        file_uploader=file_uploader,
        session_manager=session_manager,
        progress_indicator=progress_indicator,
        letter_editor=letter_editor,
        mirror_match_service=mirror_match_service,
        ats_analyzer_service=ats_analyzer_service,
        smart_coach_service=smart_coach_service,
        trajectory_builder_service=trajectory_builder_service,
        job_offer_parser=job_offer_parser
    )
    about_page = AboutPage()
    premium_page = PremiumPage()
    settings_page = SettingsPage()

    render_api_monitoring_dashboard()

    tabs = st.tabs([
        "Générateur de Lettres", "Offres Premium", "Paramètres", "À Propos", "Dev Monitoring"
    ])
    
    with tabs[0]:
        generator_page.render()
    with tabs[1]:
        premium_page.render()
    with tabs[2]:
        settings_page.render()
    with tabs[3]:
        about_page.render()
    with tabs[4]:
        render_detailed_monitoring()
        if st.checkbox("Mode Debug - Diagnostic 50 Requêtes"):
            diagnostic_urgence_50_requetes()

# --- Aiguilleur Principal ---

def main():
    """Point d'entrée et aiguilleur principal de l'application."""
    st.set_page_config(layout="wide", page_title="Phoenix Letters")
    
    settings = Settings()

    # 🚀 GESTION SSO PHOENIX (Priorité absolue)
    phoenix_user = phoenix_sso.handle_streamlit_sso('letters')
    
    if phoenix_user:
        # Utilisateur connecté via SSO Phoenix - Priorité maximale
        logger.info(f"Utilisateur Phoenix SSO authentifié: {phoenix_user.get('email')}")
        
        # Synchronisation profil Phoenix
        phoenix_sso.sync_user_profile(phoenix_user, 'letters')
        
        # Affichage badge utilisateur Phoenix
        show_phoenix_user_badge()
        
        # Navigation Phoenix dans sidebar
        render_phoenix_navigation('letters')
        
        # Configuration utilisateur Phoenix
        st.session_state.user_id = phoenix_user.get('user_id')
        st.session_state.user_email = phoenix_user.get('email')
        st.session_state.user_tier = UserTier.PREMIUM if phoenix_user.get('user_tier') == 'premium' else UserTier.FREE
        st.session_state.auth_flow_choice = 'phoenix_sso'
        
        # Rendu application avec données Phoenix
        render_main_app(phoenix_user, None, settings, phoenix_mode=True)
        return

    if 'async_service_runner' not in st.session_state:
        st.session_state.async_service_runner = AsyncServiceRunner()
        st.session_state.async_service_runner.start()

    @st.cache_resource
    def get_db_connection(_settings: Settings) -> DatabaseConnection:
        """Initialise et retourne une connexion à la base de données."""
        return DatabaseConnection(_settings)

    db_connection = get_db_connection(settings)
    jwt_manager = JWTManager(settings)
    auth_service = UserAuthService(jwt_manager, db_connection)
    auth_middleware = StreamlitAuthMiddleware(auth_service, jwt_manager)

    current_user = auth_middleware.get_current_user()

    if 'auth_flow_choice' not in st.session_state:
        st.session_state.auth_flow_choice = None

    # Aiguillage (mode classique si pas de SSO Phoenix)
    if current_user is None and st.session_state.auth_flow_choice is None:
        render_choice_page()
    elif current_user is None and st.session_state.auth_flow_choice == 'login':
        render_login_page(auth_middleware)
    else: # L'utilisateur est soit connecté, soit en mode invité
        render_main_app(current_user, auth_middleware, settings, phoenix_mode=False)

if __name__ == "__main__":
    main()
