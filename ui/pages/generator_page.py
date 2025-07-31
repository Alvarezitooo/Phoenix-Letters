"""Page principale de génération de lettres."""
import streamlit as st
from typing import Optional
import logging
import time

from core.entities.letter import GenerationRequest, ToneType, UserTier
from core.services.letter_service import LetterService
from core.services.job_offer_parser import JobOfferParser
from ui.components.file_uploader import SecureFileUploader
from ui.components.progress_bar import ProgressIndicator
from ui.components.letter_editor import LetterEditor
from ui.components.premium_results_renderer import PremiumResultsRenderer, MetricCard, ResultSection
from ui.components.conversion_popup import ConversionPopup
from ui.components.premium_barriers import PremiumBarrier, SmartUpgradePrompts
from core.services.conversion_optimizer import ConversionOptimizer
from infrastructure.storage.session_manager import SecureSessionManager
from shared.exceptions.specific_exceptions import LetterGenerationError, ValidationError

logger = logging.getLogger(__name__)

class GeneratorPage:
    """Page de génération de lettres modulaire."""
    
    def __init__(
        self,
        letter_service: LetterService,
        file_uploader: SecureFileUploader,
        session_manager: SecureSessionManager,
        progress_indicator: ProgressIndicator,
        letter_editor: LetterEditor,
        mirror_match_service,
        ats_analyzer_service,
        smart_coach_service,
        trajectory_builder_service,
        job_offer_parser: JobOfferParser = None
    ):
        self.letter_service = letter_service
        self.file_uploader = file_uploader
        self.session_manager = session_manager
        self.progress_indicator = progress_indicator
        self.letter_editor = letter_editor
        self.mirror_match_service = mirror_match_service
        self.ats_analyzer_service = ats_analyzer_service
        self.smart_coach_service = smart_coach_service
        self.trajectory_builder_service = trajectory_builder_service
        # Initialisation sécurisée du parser
        self.job_offer_parser = job_offer_parser or JobOfferParser()
        # Renderer pour résultats Premium
        self.premium_renderer = PremiumResultsRenderer()
        # Composant conversion Premium
        self.conversion_popup = ConversionPopup()
        # Optimiseur de conversion
        self.conversion_optimizer = ConversionOptimizer()
    
    def render(self) -> None:
        """Affiche la page de génération."""
        st.markdown("### 🚀 Générateur de Lettres Phoenix")
        
        # Indicateur de progression
        progress = self.session_manager.get('generation_progress', 0)
        self.progress_indicator.render(progress, "Progression de la génération")
        
        # Section d'upload de fichiers
        self._render_file_upload_section()
        
        # Configuration IA
        if self._has_required_files():
            self._render_ai_configuration()
            self._render_advanced_features() # Appel de la nouvelle méthode

        # Affichage de la lettre générée
        self._render_generated_letter()
    
    def _render_file_upload_section(self) -> None:
        """Affiche la section d'upload de fichiers."""
        col1, col2 = st.columns(2)
        
        with col1:
            cv_content = self.file_uploader.render(
                label="📄 Votre CV",
                accepted_types=['pdf', 'txt'],
                key="cv_upload",
                help_text="Votre CV au format PDF ou TXT",
                on_upload=self._on_cv_upload
            )
            
            if cv_content:
                self.session_manager.set('cv_content', cv_content.decode('utf-8', errors='ignore'))
        
        with col2:
            job_offer_content = self.file_uploader.render(
                label="📋 Offre d'emploi",
                accepted_types=['txt', 'pdf'],
                key="job_offer_upload",
                help_text="L'offre d'emploi au format TXT ou PDF",
                on_upload=self._on_job_offer_upload
            )
            
            if job_offer_content:
                self.session_manager.set('job_offer_content', job_offer_content.decode('utf-8', errors='ignore'))
    
    def _render_ai_configuration(self) -> None:
        """Affiche la configuration IA avec compteur d'usage."""
        st.markdown("### ⚙️ Configuration de l'IA")
        
        # Affichage compteur usage pour utilisateurs FREE
        self._render_usage_counter()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sélection du ton
            tone_options = [tone.value for tone in ToneType]
            selected_tone = st.selectbox(
                "🎭 Ton souhaité",
                options=tone_options,
                index=tone_options.index(self.session_manager.get('selected_tone', 'formel')),
                key="tone_selector"
            )
            self.session_manager.set('selected_tone', selected_tone)
        
        with col2:
            # Reconversion - Toujours activée pour cette niche
            # Suppression de la checkbox
            pass # Placeholder pour maintenir la structure des colonnes si nécessaire
        
        # Configuration reconversion - toujours affichée
        self.session_manager.set('is_career_change', True) # Force la reconversion à True
        self._render_career_change_config()

        # Bouton de génération déplacé ici
        if self._render_generation_button():
            self._process_generation()
    
    def _render_career_change_config(self) -> None:
        """Affiche la configuration spécifique à la reconversion."""
        st.markdown("#### 🔄 **Votre Parcours de Reconversion**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            old_domain = st.text_input(
                "📈 Ancien domaine",
                value=self.session_manager.get('old_domain', ''),
                placeholder="Ex: Marketing, Comptabilité",
                key="old_domain_input"
            )
            self.session_manager.set('old_domain', old_domain)
        
        with col2:
            new_domain = st.text_input(
                "🎯 Nouveau domaine",
                value=self.session_manager.get('new_domain', ''),
                placeholder="Ex: Cybersécurité, Développement",
                key="new_domain_input"
            )
            self.session_manager.set('new_domain', new_domain)
        
        # Compétences transférables
        # Assurez-vous que la clé existe dans st.session_state avant de l'utiliser
        if 'transferable_skills' not in st.session_state:
            st.session_state.transferable_skills = self.session_manager.get('transferable_skills', '')

        transferable_skills = st.text_area(
            "🔧 Compétences transférables",
            value=st.session_state.transferable_skills, # Lire directement depuis st.session_state
            help="Listez les compétences de votre ancienne carrière pertinentes pour le nouveau poste",
            key="transferable_skills"
        )

        # Afficher le bouton de suggestion de compétences uniquement si les domaines sont renseignés
        if old_domain and new_domain:
            if st.button("✨ Suggérer les compétences", key="suggest_skills_button", use_container_width=True):
                self._process_skills_suggestion()
        else:
            st.info("Renseignez l'ancien et le nouveau domaine pour suggérer des compétences.")

    def _process_skills_suggestion(self) -> None:
        """
        Traite la suggestion de compétences transférables.
        """
        old_domain = self.session_manager.get('old_domain')
        new_domain = self.session_manager.get('new_domain')
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))

        if not old_domain or not new_domain:
            st.warning("Veuillez renseigner l'ancien et le nouveau domaine pour suggérer des compétences.")
            return

        with st.spinner("🧠 L'IA analyse vos domaines pour suggérer des compétences..."):
            try:
                suggestions = self.letter_service.suggest_transferable_skills(old_domain, new_domain, user_tier)
                self.session_manager.set('transferable_skills', suggestions)
                
                st.success("✅ Suggestions de compétences générées !")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la suggestion de compétences: {e}")
                logger.error(f"Error suggesting skills: {e}")

    def _render_advanced_features(self) -> None:
        """Affiche les fonctionnalités avancées (Mirror Match, ATS, Smart Coach, Trajectory Builder)."""
        st.markdown("### 🌟 Fonctionnalités Avancées")

        user_tier = st.session_state.get('user_tier', UserTier.FREE)
        is_premium = user_tier != UserTier.FREE

        # Mirror Match
        with st.expander("🎭 Mirror Match - Adaptez le ton à l'entreprise"):
            st.markdown("Analysez la culture de l'entreprise pour adapter le ton de votre lettre.")
            if not is_premium:
                st.info("Cette fonctionnalité est réservée aux utilisateurs Premium.")
            company_culture_info = st.text_area(
                "Informations sur l'entreprise (site web, valeurs, etc.)",
                key="company_culture_info",
                help="Collez ici des informations qui décrivent la culture de l'entreprise.",
                disabled=not is_premium
            )
            if st.button("Analyser la culture", key="analyze_culture_button", disabled=not is_premium):
                self._process_mirror_match(company_culture_info)

        # ATS Analyzer
        with st.expander("🔍 ATS Analyzer - Optimisez pour les recruteurs"):
            st.markdown("Évaluez la compatibilité de votre lettre avec les systèmes de tri automatique.")
            if not is_premium:
                st.info("Cette fonctionnalité est réservée aux utilisateurs Premium.")
            target_sector = st.selectbox(
                "Secteur cible (pour une analyse plus précise)",
                options=["Général", "Tech", "Marketing", "Finance", "RH", "Santé"],
                key="ats_target_sector",
                disabled=not is_premium
            )
            if st.button("Analyser la compatibilité ATS", key="analyze_ats_button", disabled=not is_premium):
                self._process_ats_analysis(target_sector)

        # Smart Coach
        with st.expander("🧠 Smart Coach - Feedback IA détaillé"):
            st.markdown("Obtenez une analyse qualitative de votre lettre et des suggestions d'amélioration.")
            if not is_premium:
                st.info("Cette fonctionnalité est réservée aux utilisateurs Premium.")
            if st.button("Obtenir un feedback Smart Coach", key="smart_coach_button", disabled=not is_premium):
                self._process_smart_coach()

        # Trajectory Builder
        with st.expander("🗺️ Trajectory Builder - Plan de reconversion personnalisé"):
            st.markdown("Générez une feuille de route étape par étape pour votre reconversion.")
            if not is_premium:
                st.info("Cette fonctionnalité est réservée aux utilisateurs Premium.")
            if st.button("Générer mon plan de reconversion", key="trajectory_builder_button", disabled=not is_premium):
                self._process_trajectory_builder()

    def _process_mirror_match(self, company_culture_info: str) -> None:
        """Traite l'analyse Mirror Match."""
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))
        
        # Vérification Premium avec barrière intelligente
        if user_tier != UserTier.PREMIUM:
            PremiumBarrier.show_feature_lock(
                "Mirror Match",
                "Analysez la culture d'entreprise pour adapter parfaitement votre ton et approche. +89% de taux de réponse positif."
            )
            return
        
        cv_content = self.session_manager.get('cv_content')
        job_offer_content = self.session_manager.get('job_offer_content')
        if not cv_content or not job_offer_content:
            st.warning("Veuillez d'abord uploader votre CV et l'offre d'emploi.")
            return
        
        with st.spinner("Analyse de la culture d'entreprise..."):
            try:
                culture_analysis = self.mirror_match_service.analyze_company_culture(
                    company_name=self.session_manager.get('company_name', 'Entreprise Inconnue'),
                    job_offer=job_offer_content,
                    additional_info=company_culture_info,
                    user_tier=user_tier
                )
                st.success("Analyse de la culture terminée !")
                
                # Header avec renderer Premium
                self.premium_renderer.render_header(
                    "Analyse Culture d'Entreprise",
                    f"Résultats pour {culture_analysis.company_name}",
                    "🎭"
                )
                
                # Métriques principales
                metrics = [
                    MetricCard(
                        title="Confiance",
                        value=f"{culture_analysis.confidence_score:.0%}",
                        icon="🎯",
                        help_text="Niveau de fiabilité de l'analyse"
                    ),
                    MetricCard(
                        title="Secteur",
                        value=culture_analysis.industry,
                        icon="🏢"
                    ),
                    MetricCard(
                        title="Innovation",
                        value=culture_analysis.innovation_level.title(),
                        icon="💡"
                    )
                ]
                self.premium_renderer.render_metrics_row(metrics)
                
                # Indicateur de confiance
                self.premium_renderer.render_confidence_indicator(
                    culture_analysis.confidence_score,
                    "Fiabilité de l'analyse"
                )
                
                # Informations entreprise sous forme de tableau
                company_data = {
                    "style_communication": culture_analysis.communication_style,
                    "environnement_travail": culture_analysis.work_environment,
                    "style_leadership": culture_analysis.leadership_style
                }
                self.premium_renderer.render_comparison_table(
                    company_data,
                    "Profil culturel détecté"
                )
                
                # Valeurs et recommandations par sections
                sections = []
                
                if culture_analysis.values:
                    sections.append(ResultSection(
                        title="Valeurs clés identifiées",
                        content=culture_analysis.values,
                        section_type="success"
                    ))
                
                if culture_analysis.tone_recommendations:
                    sections.append(ResultSection(
                        title="Recommandations pour votre lettre",
                        content=culture_analysis.tone_recommendations,
                        section_type="info"
                    ))
                
                self.premium_renderer.render_result_sections(sections)
                
                # Nuage de mots-clés culturels si disponible
                if hasattr(culture_analysis, 'cultural_keywords') and culture_analysis.cultural_keywords:
                    self.premium_renderer.render_keyword_cloud(
                        culture_analysis.cultural_keywords,
                        "Mots-clés culturels détectés"
                    )
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse de la culture : {e}")
                logger.error(f"Mirror Match error: {e}")
                
                # Suggestions d'amélioration en cas d'erreur
                st.info("💡 **Conseils pour une meilleure analyse:**")
                st.write("• Ajoutez plus d'informations sur l'entreprise (site web, valeurs affichées)")
                st.write("• Vérifiez que l'offre d'emploi contient suffisamment de détails")
                st.write("• Essayez avec une offre provenant directement du site de l'entreprise")

    def _process_ats_analysis(self, target_sector: str) -> None:
        """Traite l'analyse ATS."""
        letter_content = self.session_manager.get('generated_letter')
        job_offer_content = self.session_manager.get('job_offer_content')
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))
        if not letter_content or not job_offer_content:
            st.warning("Veuillez d'abord générer une lettre et uploader l'offre d'emploi.")
            return

        with st.spinner("Analyse de compatibilité ATS..."):
            try:
                ats_analysis = self.ats_analyzer_service.analyze_ats_compatibility(
                    letter_content=letter_content,
                    job_description=job_offer_content,
                    target_sector=target_sector if target_sector != "Général" else None,
                    user_tier=user_tier
                )
                st.success("✅ Analyse ATS terminée !")
                
                # Header professionnel
                self.premium_renderer.render_header(
                    "Analyse ATS (Applicant Tracking System)",
                    "Optimisation pour les systèmes de recrutement automatisés",
                    "🔍"
                )
                
                # Métriques ATS principales
                ats_metrics = [
                    MetricCard(
                        title="Compatibilité ATS",
                        value=f"{ats_analysis.ats_compatibility_score:.1f}%",
                        delta="+15%" if ats_analysis.ats_compatibility_score > 70 else None,
                        icon="🎯",
                        help_text="Score global de compatibilité avec les ATS"
                    ),
                    MetricCard(
                        title="Formatage",
                        value=f"{ats_analysis.formatting_score:.1f}%",
                        icon="📄",
                        help_text="Qualité du formatage pour lecture automatique"
                    ),
                    MetricCard(
                        title="Verbes d'Action",
                        value=f"{ats_analysis.action_verbs_score:.1f}%",
                        icon="⚡",
                        help_text="Utilisation de verbes d'action impactants"
                    ),
                    MetricCard(
                        title="Accomplissements",
                        value=str(ats_analysis.quantifiable_achievements_count),
                        icon="📈",
                        help_text="Nombre d'accomplissements quantifiés"
                    )
                ]
                self.premium_renderer.render_metrics_row(ats_metrics)
                
                # Jauge de score principal
                self.premium_renderer.render_score_gauge(
                    ats_analysis.ats_compatibility_score,
                    "Score de compatibilité ATS",
                    100
                )
                
                # Mots-clés trouvés (nuage vert)
                if ats_analysis.matched_keywords:
                    st.markdown("### ✅ Mots-clés détectés")
                    self.premium_renderer.render_keyword_cloud(
                        ats_analysis.matched_keywords,
                        "Mots-clés du poste présents dans votre lettre"
                    )
                
                # Sections organisées
                sections = []
                
                if ats_analysis.missing_keywords:
                    sections.append(ResultSection(
                        title="Mots-clés manquants à intégrer",
                        content=ats_analysis.missing_keywords[:5],  # Limite à 5 pour lisibilité
                        section_type="warning"
                    ))
                
                if ats_analysis.recommendations:
                    sections.append(ResultSection(
                        title="Recommandations d'optimisation",
                        content=ats_analysis.recommendations,
                        section_type="info"
                    ))
                
                self.premium_renderer.render_result_sections(sections)
                
                # Actions recommandées si score faible
                if ats_analysis.ats_compatibility_score < 50:
                    actions = [
                        {
                            'label': '🚀 Générer version optimisée',
                            'type': 'primary'
                        },
                        {
                            'label': '📈 Voir guide ATS',
                            'type': 'secondary'
                        }
                    ]
                    self.premium_renderer.render_action_buttons(actions)
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse ATS : {e}")
                logger.error(f"ATS Analysis error: {e}")
                
                # Guide de dépannage
                with st.expander("💡 Guide de dépannage ATS"):
                    st.markdown("""
                    **Causes possibles d'erreur :**
                    - Lettre trop courte (< 200 mots)
                    - Offre d'emploi incomplète ou non structurée
                    - Contenu avec caractères spéciaux non supportés
                    
                    **Solutions recommandées :**
                    - Vérifiez que votre lettre fait au moins 250 mots
                    - Utilisez une offre d'emploi détaillée
                    - Évitez les caractères spéciaux dans le texte
                    """)

    def _process_smart_coach(self) -> None:
        """Traite le feedback Smart Coach."""
        letter_content = self.session_manager.get('generated_letter')
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))
        if not letter_content:
            st.warning("Veuillez d'abord générer une lettre.")
            return

        with st.spinner("Obtention du feedback Smart Coach..."):
            try:
                feedback = self.smart_coach_service.analyze_letter_real_time(letter_content, user_tier=user_tier)
                st.success("🎆 Feedback Smart Coach obtenu !")
                
                # Header avec coaching tone
                self.premium_renderer.render_header(
                    "Smart Coach - Analyse Qualitative",
                    "Feedback détaillé et recommandations personnalisées",
                    "🧠"
                )
                st.write(f"**Score global de votre lettre :** {feedback.overall_score:.1f}%")
                st.write(f"**Clarté :** {feedback.clarity_score:.1f}%")
                st.write(f"**Impact :** {feedback.impact_score:.1f}%")
                st.write(f"**Personnalisation :** {feedback.personalization_score:.1f}%")
                st.write(f"**Ton professionnel :** {feedback.professional_tone_score:.1f}%")

                if feedback.positive_points:
                    st.markdown("**Points forts de votre lettre :**")
                    for point in feedback.positive_points:
                        st.write(f"- {point}")
                
                if feedback.critical_issues:
                    st.markdown("**Problèmes critiques à corriger :**")
                    for issue in feedback.critical_issues:
                        st.write(f"- {issue}")
                
                if feedback.specific_suggestions:
                    st.markdown("**Suggestions d'amélioration :**")
                    for suggestion in feedback.specific_suggestions:
                        st.write(f"- {suggestion['text']} (Priorité: {suggestion['priority']})")
                
                st.markdown("**Prochaines étapes :**")
                for step in feedback.next_steps:
                    st.write(f"- {step}")
                
                st.write(f"*Temps de lecture estimé : {feedback.estimated_read_time} secondes*.")

                if feedback.overall_score < 60:
                    st.warning("Votre lettre nécessite des améliorations significatives. Suivez les suggestions ci-dessus.")
            except Exception as e:
                st.error(f"Erreur lors du feedback Smart Coach : {e}")
                logger.error(f"Smart Coach error: {e}")

    def _process_trajectory_builder(self) -> None:
        """Traite la génération du plan de reconversion."""
        # Pour simplifier, nous allons utiliser des données de session ou des inputs basiques pour le moment
        # Idéalement, cela devrait être une page ou un formulaire plus complexe
        user_id = self.session_manager.get('user_id', 'default_user')
        current_role = st.session_state.get('old_domain', 'Ancien Rôle')
        target_role = st.session_state.get('new_domain', 'Nouveau Rôle')
        current_skills = self.session_manager.get('transferable_skills', '').split(',')
        current_skills = [s.strip() for s in current_skills if s.strip()]
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))

        if not current_role or not target_role or not current_skills:
            st.warning("Veuillez renseigner votre ancien/nouveau domaine et vos compétences transférables dans la section 'Reconversion'.")
            return

        with st.spinner("Génération de votre plan de reconversion..."):
            try:
                reconversion_plan = self.trajectory_builder_service.create_reconversion_plan(
                    user_id=user_id,
                    current_role=current_role,
                    target_role=target_role,
                    current_skills=current_skills,
                    user_tier=user_tier
                )
                st.success("🎯 Plan de reconversion généré !")
                
                # Header professionnel
                self.premium_renderer.render_header(
                    "Trajectory Builder - Votre Feuille de Route",
                    f"Plan personnalisé {current_role} → {target_role}",
                    "🗺️"
                )
                st.write(f"**Durée estimée :** {reconversion_plan.estimated_duration_months} mois")
                st.write(f"**Probabilité de succès :** {reconversion_plan.success_probability:.0%}")
                st.write(f"**Niveau de difficulté estimé :** {reconversion_plan.difficulty_level.capitalize()}")

                st.markdown("##### Lacunes en compétences identifiées :")
                if reconversion_plan.skill_gaps:
                    for gap in reconversion_plan.skill_gaps:
                        st.write(f"- {gap}")
                else:
                    st.info("Aucune lacune majeure en compétences identifiée. Excellent !")

                st.markdown("##### Étapes clés de votre parcours :")
                for step in reconversion_plan.trajectory_steps:
                    st.markdown(f"**Étape {step.step_number}: {step.title}** ({step.duration_weeks} semaines)")
                    st.write(f"  - {step.description}")
                    if step.skills_to_develop:
                        st.write(f"  - Compétences à développer : {', '.join(step.skills_to_develop)}")
                    if step.milestones:
                        st.write(f"  - Jalons : {', '.join(step.milestones)}")
                    if step.resources:
                        st.write(f"  - Ressources : {', '.join(step.resources)}")

                if reconversion_plan.recommended_resources:
                    st.markdown("##### Ressources Recommandées :")
                    for res in reconversion_plan.recommended_resources:
                        st.write(f"- [{res.get('name', 'Lien')}]({res.get('url', '#')}) ({res.get('type', 'Général')})")

                if reconversion_plan.industry_insights:
                    st.markdown("##### Insights Sectoriels :")
                    for key, value in reconversion_plan.industry_insights.items():
                        st.write(f"- **{key.replace('_', ' ').capitalize()} :** {value}")
            except Exception as e:
                st.error(f"Erreur lors de la génération du plan de reconversion : {e}")
                logger.error(f"Trajectory Builder error: {e}")

    def _render_generation_button(self) -> bool:
        """Affiche le bouton de génération et retourne True si cliqué."""
        # Vérification du cooldown
        last_generation = self.session_manager.get('last_generation_time', 0)
        current_time = time.time()
        cooldown_remaining = max(0, 60 - (current_time - last_generation))
        
        if cooldown_remaining > 0:
            st.button(
                f"⏳ Attendre {int(cooldown_remaining)}s",
                disabled=True,
                use_container_width=True
            )
            return False
        
        return st.button(
            "✨ Générer ma lettre",
            type="primary",
            use_container_width=True,
            key="generate_button"
        )
    
    def _process_generation(self) -> None:
        """Traite la génération de lettre."""
        try:
            # Mise à jour du progress
            self.session_manager.set('generation_progress', 25)
            
            with st.spinner("🤖 Génération en cours..."):
                # Construction de la requête
                request = self._build_generation_request()

                # Vérification spécifique pour la reconversion
                if request.is_career_change and (not request.old_domain or not request.new_domain):
                    st.error("❌ Veuillez renseigner l'ancien et le nouveau domaine pour la reconversion.")
                    self.session_manager.set('generation_progress', 0)
                    return
                
                # Génération de la lettre
                self.session_manager.set('generation_progress', 75)
                user_id = self.session_manager.get('user_id', 'default_user_id')
                letter = self.letter_service.generate_letter(request, user_id)
                
                # Sauvegarde
                self.session_manager.set('generated_letter', letter.content)
                self.session_manager.set('generation_progress', 100)
                self.session_manager.set('last_generation_time', time.time())
                
                st.success("✅ Lettre générée avec succès!")
                
                # Upsell contextuel post-génération
                user_tier = UserTier(self.session_manager.get('user_tier', 'free'))
                if user_tier == UserTier.FREE:
                    # Compter lettres générées pour upsell contextuel
                    generation_count = self.session_manager.get('generation_count', 0) + 1
                    self.session_manager.set('generation_count', generation_count)
                    
                    if self.conversion_popup.show_success_upsell(generation_count):
                        st.switch_page("Offres Premium")
                
        except ValidationError as e:
            st.error(f"❌ Erreur de validation: {e}")
            logger.warning(f"Validation error in generation: {e}")
        except LetterGenerationError as e:
            st.error(f"❌ Erreur de génération: {e}")
            logger.error(f"Generation error: {e}")
        except Exception as e:
            st.error("❌ Erreur inattendue lors de la génération")
            logger.error(f"Unexpected error in generation: {e}")
        finally:
            # Reset du progress en cas d'erreur
            if self.session_manager.get('generation_progress', 0) != 100:
                self.session_manager.set('generation_progress', 0)
    
    def _render_generated_letter(self) -> None:
        """Affiche la lettre générée."""
        generated_letter = self.session_manager.get('generated_letter')
        
        if generated_letter:
            st.markdown("---")
            st.markdown("### ✨ Votre Lettre Phoenix Générée")
            
            # Éditeur de lettre
            edited_letter = self.letter_editor.render(
                content=generated_letter,
                key="letter_editor"
            )
            
            # Sauvegarde des modifications
            if edited_letter != generated_letter:
                self.session_manager.set('generated_letter', edited_letter)
    
    # Méthodes utilitaires
    def _has_required_files(self) -> bool:
        """Vérifie si les fichiers requis sont présents."""
        return (
            self.session_manager.get('cv_content') and 
            self.session_manager.get('job_offer_content')
        )
    
    def _build_generation_request(self) -> GenerationRequest:
        """Construit la requête de génération avec parser sécurisé."""
        job_offer_content = self.session_manager.get('job_offer_content')
        
        # Utilisation du JobOfferParser sécurisé
        try:
            job_details = self.job_offer_parser.extract_job_details(job_offer_content)
            job_title = job_details.job_title or "Poste non spécifié"
            company_name = job_details.company_name or "Entreprise non spécifiée"
        except Exception as e:
            logger.warning(f"Job details extraction failed: {e}")
            job_title = "Poste non spécifié"
            company_name = "Entreprise non spécifiée"

        return GenerationRequest(
            cv_content=self.session_manager.get('cv_content'),
            job_offer_content=job_offer_content,
            job_title=job_title,
            company_name=company_name,
            tone=ToneType(self.session_manager.get('selected_tone', 'formel')),
            user_tier=UserTier(self.session_manager.get('user_tier', 'free')),
            is_career_change=self.session_manager.get('is_career_change', False),
            old_domain=self.session_manager.get('old_domain'),
            new_domain=self.session_manager.get('new_domain'),
            transferable_skills=self.session_manager.get('transferable_skills')
        )
    
    def _on_cv_upload(self, filename: str, content: bytes) -> None:
        """Callback appelé lors de l'upload du CV."""
        self.session_manager.set('generation_progress', 33)
        logger.info(f"CV uploaded: {filename}")
    
    def _on_job_offer_upload(self, filename: str, content: bytes) -> None:
        """Callback appelé lors de l'upload de l'offre."""
        current_progress = self.session_manager.get('generation_progress', 0)
        self.session_manager.set('generation_progress', max(current_progress, 66))
        logger.info(f"Job offer uploaded: {filename}")
    
    def _render_usage_counter(self) -> None:
        """Affiche le compteur d'usage pour les utilisateurs FREE."""
        user_tier = UserTier(self.session_manager.get('user_tier', 'free'))
        
        if user_tier == UserTier.FREE:
            remaining = self.letter_service.get_remaining_generations(user_tier)
            
            if remaining is not None:
                # Interface utilisateur attractive
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if remaining > 0:
                        st.info(f"📊 **{remaining}/2 lettres restantes** ce mois (utilisateur Free)")
                    else:
                        st.error("❌ **Limite atteinte** - 0/2 lettres restantes ce mois")
                
                with col2:
                    # Call-to-action Premium contextuel avec animation
                    if remaining <= 1:
                        if st.button("🚀 Passer Premium", use_container_width=True, type="primary", help="Génération illimitée + fonctionnalités avancées"):
                            st.balloons()  # Animation célébration
                            st.success("Redirection vers les offres Premium...")
                            st.switch_page("Offres Premium")
                
                # Barre de progression visuelle
                progress_value = max(0, remaining) / 2
                st.progress(progress_value, text=f"Usage mensuel: {2-remaining}/2")
                
                if remaining == 0:
                    # Afficher popup conversion optimisé
                    if self.conversion_popup.show_limit_reached_popup():
                        st.switch_page("Offres Premium")
                    st.warning("💡 **Astuce**: Passez Premium pour une génération illimitée de lettres !")
        else:
            # Utilisateurs Premium - Badge status
            st.success("✨ **Utilisateur Premium** - Génération illimitée active")
            st.caption("🎯 Accès complet à toutes les fonctionnalités avancées")