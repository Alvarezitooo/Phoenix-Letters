"""Composant popup de conversion Free → Premium."""
import streamlit as st
from typing import Optional


class ConversionPopup:
    """Popup optimisé pour conversion Premium."""
    
    def __init__(self):
        self.session_key_shown = "conversion_popup_shown"
    
    def show_limit_reached_popup(self) -> bool:
        """
        Affiche popup quand limite Free atteinte.
        Returns: True si CTA cliqué, False sinon
        """
        
        # Éviter spam - montrer max 1 fois par session
        if st.session_state.get(self.session_key_shown, False):
            return False
        
        # Modal avec urgence et bénéfices
        st.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.7); z-index: 999; display: flex; 
                    align-items: center; justify-content: center;">
            <div style="background: white; padding: 2rem; border-radius: 20px; 
                        max-width: 500px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                <h2 style="color: #ff6b35; margin-bottom: 1rem;">🚫 Limite Atteinte !</h2>
                <p style="font-size: 1.2rem; margin-bottom: 1.5rem;">
                    Vous avez utilisé vos <strong>2 lettres gratuites</strong> ce mois.
                </p>
                <div style="background: #fff8dc; padding: 1rem; border-radius: 10px; margin-bottom: 1.5rem;">
                    <h3 style="color: #28a745; margin: 0;">🚀 Débloquez MAINTENANT</h3>
                    <p style="margin: 0.5rem 0;"><strong>Lettres ILLIMITÉES</strong></p>
                    <p style="margin: 0;"><span style="text-decoration: line-through;">29€</span> 
                       <strong style="color: #28a745; font-size: 1.5rem;">19€/mois</strong></p>
                    <p style="color: #ff6b35; font-size: 0.9rem; margin: 0;">⏰ Offre limitée -33%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # CTA principal
            if st.button(
                "🚀 PASSER PREMIUM MAINTENANT", 
                use_container_width=True, 
                type="primary",
                key="popup_cta_premium"
            ):
                st.session_state[self.session_key_shown] = True
                self._track_event("popup_conversion_clicked")
                return True
            
            # Lien alternative
            if st.button(
                "⏰ Rappel dans 7 jours", 
                use_container_width=True,
                key="popup_remind_later"
            ):
                st.session_state[self.session_key_shown] = True
                self._track_event("popup_remind_later")
                st.info("📅 Nous vous rappellerons le mois prochain !")
                return False
        
        return False
    
    def show_feature_locked_popup(self, feature_name: str) -> bool:
        """
        Popup quand utilisateur Free tente d'accéder fonctionnalité Premium.
        
        Args:
            feature_name: Nom de la fonctionnalité (ex: "Mirror Match")
        Returns: True si conversion déclenchée
        """
        
        st.warning(f"🔒 **{feature_name}** est une fonctionnalité Premium")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"""
            ### 🎯 Avec {feature_name} Premium:
            - Analyses approfondies IA
            - Personnalisation avancée  
            - Résultats détaillés
            - Support prioritaire
            """)
        
        with col2:
            st.markdown("""
            ### 💰 Offre Spéciale
            <div style="text-align: center;">
                <span style="text-decoration: line-through;">29€/mois</span><br>
                <span style="color: #28a745; font-size: 2rem; font-weight: bold;">19€/mois</span><br>
                <span style="color: #ff6b35;">🎉 -33% Lancement</span>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button(
            f"🚀 Débloquer {feature_name} + Toutes les fonctionnalités", 
            use_container_width=True, 
            type="primary",
            key=f"unlock_{feature_name.lower().replace(' ', '_')}"
        ):
            self._track_event("feature_unlock_clicked", {"feature": feature_name})
            st.balloons()
            st.success("🎉 Redirection vers Premium...")
            return True
        
        return False
    
    def show_success_upsell(self, letter_count: int) -> bool:
        """
        Upsell subtil après génération réussie.
        
        Args:
            letter_count: Nombre de lettres générées par l'utilisateur
        Returns: True si intérêt Premium exprimé
        """
        
        if letter_count == 1:  # Première lettre
            st.success("🎉 **Première lettre générée avec succès !**")
            
            with st.expander("💡 Conseil Pro - Maximisez vos chances"):
                st.markdown("""
                **Votre lettre est bonne, mais elle pourrait être PARFAITE !**
                
                Avec **Premium**, cette même lettre aurait bénéficié de :
                - 🎯 **Mirror Match** : Adaptation parfaite à la culture d'entreprise
                - 🤖 **ATS Analyzer** : Optimisation pour les filtres automatiques  
                - 🧠 **Smart Coach** : Feedback détaillé pour amélioration
                
                **Résultat** : +89% de taux de réponse vs lettres standard
                """)
                
                if st.button("🚀 Voir Premium (19€/mois)", key="success_upsell_1"):
                    self._track_event("success_upsell_clicked", {"letter_count": letter_count})
                    return True
        
        elif letter_count == 2:  # Dernière lettre gratuite
            st.warning("⚠️ **Dernière lettre gratuite utilisée !**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                🎯 **Vous maîtrisez Phoenix Letters !** 
                
                Pour continuer votre reconversion avec succès :
                - **Lettres illimitées** pour postuler sans limite
                - **Outils Premium** pour maximiser vos chances
                - **Support 24/7** pour vous accompagner
                """)
            
            with col2:
                if st.button("🚀 Continuer en Premium", type="primary", key="success_upsell_2"):
                    self._track_event("success_upsell_clicked", {"letter_count": letter_count})
                    return True
        
        return False
    
    def _track_event(self, event: str, properties: Optional[dict] = None):
        """Track conversion events."""
        try:
            import streamlit as st
            from core.services.analytics_service import AnalyticsService
            
            analytics = AnalyticsService()
            user_id = st.session_state.get('user_id', 'anonymous')
            user_tier = st.session_state.get('user_tier', 'free')
            
            analytics.track_conversion_funnel(
                step=event,
                user_id=user_id,
                user_tier=user_tier,
                source="popup",
                properties=properties
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Analytics tracking failed: {e}")