import streamlit as st
import logging
import asyncio
from datetime import datetime

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
from utils.async_runner import AsyncServiceRunner # Import du nouveau runner

from core.entities.user import UserTier
from infrastructure.auth.jwt_manager import JWTManager
from infrastructure.auth.user_auth_service import UserAuthService
from infrastructure.auth.streamlit_auth_middleware import StreamlitAuthMiddleware
from infrastructure.database.db_connection import DatabaseConnection

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(layout="wide", page_title="Phoenix Letters")
    
    settings = Settings()

    # Gérer l'instance du service asynchrone dans st.session_state pour persister
    if 'async_service_runner' not in st.session_state:
        st.session_state.async_service_runner = AsyncServiceRunner()
        st.session_state.async_service_runner.start()

    @st.cache_resource
    def get_db_connection(settings: Settings):
        db_conn = DatabaseConnection(settings)
        # Utiliser le runner pour initialiser la DB de manière asynchrone
        st.session_state.async_service_runner.run_coro_in_thread(db_conn.initialize()).result()
        return db_conn

    db_connection = get_db_connection(settings)
    jwt_manager = JWTManager(settings)
    auth_service = UserAuthService(jwt_manager, db_connection)
    auth_middleware = StreamlitAuthMiddleware(auth_service, jwt_manager)

    # Vérifier si l'utilisateur est connecté
    current_user = auth_middleware.get_current_user()

    # Gérer le choix initial de l'utilisateur (invité ou connexion)
    if 'auth_flow_choice' not in st.session_state:
        st.session_state.auth_flow_choice = None

    if current_user is None and st.session_state.auth_flow_choice is None:
        st.title("🔥 Phoenix Letters")
        st.write("Bienvenue sur Phoenix Letters, votre assistant pour des lettres de motivation percutantes.")
        st.write("Choisissez comment vous souhaitez commencer :")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Commencer ma lettre (gratuit)", use_container_width=True, key="guest_access_button"):
                st.session_state.auth_flow_choice = 'guest'
                st.session_state.guest_user_id = f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}" # Temporary guest ID
                st.session_state.user_tier = UserTier.FREE # Set guest tier
                st.rerun()
        with col2:
            if st.button("🔑 Se connecter / S'inscrire", use_container_width=True, key="login_register_button"):
                st.session_state.auth_flow_choice = 'login'
                st.rerun()
        st.stop() # Stop execution until a choice is made

    # Si l'utilisateur a choisi de se connecter et n'est pas encore connecté
    if current_user is None and st.session_state.auth_flow_choice == 'login':
        st.title("🔥 Phoenix Letters - Connexion / Inscription")
        auth_middleware.login_form()
        st.stop() # Stop execution until login/registration is complete

    # Si l'utilisateur est connecté (via login)
    if current_user:
        st.title(f"🔥 Phoenix Letters - Bienvenue, {current_user.email}")
        if st.sidebar.button("Se déconnecter"):
            auth_middleware.logout()
            st.rerun()
    # Si l'utilisateur est en mode invité
    elif st.session_state.auth_flow_choice == 'guest':
        st.title("🔥 Phoenix Letters - Mode Invité")
        st.sidebar.info(
            "🚀 **Débloquez tout le potentiel de Phoenix Letters !**\n\n"\
            "En créant un compte gratuit, vous pourrez :\n"\
            "- **Sauvegarder** et retrouver toutes vos lettres\n"\
            "- Accéder à l'**historique** de vos générations\n"\
            "- Bénéficier de **fonctionnalités Premium** exclusives (bientôt !)\n"\
            "- Recevoir des **conseils personnalisés** pour votre carrière\n\n"\
            "**N'attendez plus, inscrivez-vous !**"
        )
        # Set a default user_id for guest mode if not already set by the guest_access_button
        if 'user_id' not in st.session_state:
            st.session_state.user_id = st.session_state.guest_user_id
        if 'user_tier' not in st.session_state:
            st.session_state.user_tier = UserTier.FREE

    # --- AIGUILLAGE API (INTERRUPTEUR) ---
    use_mock = st.sidebar.checkbox("Utiliser le Mock API (Mode Développeur)", value=True)

    if use_mock:
        from infrastructure.ai.mock_gemini_client import MockGeminiClient
        gemini_client = MockGeminiClient()
        st.sidebar.warning("Mode Mock API activé. Aucune requête réelle ne sera envoyée.")
    else:
        gemini_client = GeminiClient(settings)
        st.sidebar.success("Mode API Réelle activé.")
    # --------------------------------------

    # Initialiser les gestionnaires et services
    session_manager = SecureSessionManager(settings)
    input_validator = InputValidator()
    performance_monitor = PerformanceMonitor()
    prompt_service = PromptService(settings)
    # Initialiser les services spécifiques
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

    # Initialiser les composants UI
    file_uploader = SecureFileUploader(input_validator, settings)
    progress_indicator = ProgressIndicator()
    letter_editor = LetterEditor()

    # Initialiser les pages avec intégration JobOfferParser
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

    # Sidebar for monitoring
    render_api_monitoring_dashboard()

    # Navigation par onglets
    tabs = st.tabs([
        "Générateur de Lettres", "Offres Premium", "Paramètres", "À Propos", "Dev Monitoring"
    ])
    
    tab_generator = tabs[0]
    tab_premium = tabs[1]
    tab_settings = tabs[2]
    tab_about = tabs[3]
    tab_monitoring = tabs[4]


    with tab_generator:
        generator_page.render()
    with tab_premium:
        premium_page.render()
    with tab_settings:
        settings_page.render()
    with tab_about:
        about_page.render()
    with tab_monitoring:
        render_detailed_monitoring()
        if st.checkbox(" Mode Debug - Diagnostic 50 Requêtes"):
            diagnostic_urgence_50_requetes()

if __name__ == "__main__":
    main()