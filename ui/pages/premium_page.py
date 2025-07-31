import streamlit as st
from typing import Optional

class PremiumPage:
    def __init__(self):
        pass

    def render(self):
        """Affiche la page Premium avec pricing et conversion optimisés."""
        
        # Header avec proposition de valeur forte
        st.markdown("""
        <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 15px; margin-bottom: 2rem; color: white;">
            <h1 style="margin: 0; font-size: 2.5rem;">🚀 Phoenix Letters Premium</h1>
            <h3 style="margin: 0.5rem 0; opacity: 0.9;">Débloquez votre potentiel de reconversion</h3>
            <p style="font-size: 1.2rem; margin: 0;">La seule plateforme IA spécialisée reconversion professionnelle</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Bénéfices quantifiés avec social proof
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("✨ Taux de réussite", "89%", "+23% vs lettres manuelles")
        
        with col2:
            st.metric("⚡ Temps économisé", "4h", "par lettre générée")
        
        with col3:
            st.metric("🎯 Utilisateurs actifs", "2,847", "+156 cette semaine")
        
        st.markdown("---")
        
        # Comparaison Free vs Premium
        st.subheader("🎯 Choisissez votre plan")
        
        col_free, col_premium = st.columns(2)
        
        with col_free:
            st.markdown("""
            ### 📝 Plan Gratuit
            **Parfait pour découvrir**
            
            ✅ **2 lettres par mois**  
            ✅ **Génération IA basique**  
            ✅ **Templates standards**  
            ❌ Mirror Match (analyse culture)  
            ❌ ATS Analyzer (optimisation CV)  
            ❌ Smart Coach (feedback détaillé)  
            ❌ Trajectory Builder (plan carrière)  
            ❌ Support prioritaire  
            
            <div style="text-align: center; margin-top: 1rem;">
                <span style="font-size: 2rem; color: #28a745;">GRATUIT</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col_premium:
            st.markdown("""
            <div style="border: 3px solid #ffd700; border-radius: 15px; padding: 1.5rem; background: #fff8dc;">
            
            ### 🏆 Plan Premium
            **<span style="color: #ff6b35;">🔥 PLUS POPULAIRE</span>**
            
            ✅ **Lettres ILLIMITÉES**  
            ✅ **IA avancée Gemini 1.5**  
            ✅ **Templates premium exclusifs**  
            ✅ **Mirror Match** - Analyse culture entreprise  
            ✅ **ATS Analyzer** - Optimisation systèmes tri  
            ✅ **Smart Coach** - Feedback IA personnalisé  
            ✅ **Trajectory Builder** - Plan reconversion  
            ✅ **Support prioritaire 24/7**  
            ✅ **Mises à jour en avant-première**
            
            <div style="text-align: center; margin-top: 1rem;">
                <span style="font-size: 1.2rem; text-decoration: line-through; color: #888;">29€/mois</span><br>
                <span style="font-size: 2.5rem; color: #28a745; font-weight: bold;">19€/mois</span><br>
                <span style="color: #ff6b35; font-weight: bold;">🎉 -33% Offre de lancement</span>
            </div>
            
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Témoignages utilisateurs
        st.subheader("💬 Ce que disent nos utilisateurs Premium")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            > *"Grâce à Phoenix Letters Premium, j'ai décroché 3 entretiens en 2 semaines ! 
            > Le Mirror Match m'a aidé à adapter parfaitement mon ton à chaque entreprise."*
            > 
            > **Sarah M.** - Transition Marketing → Tech
            """)
        
        with col2:
            st.markdown("""
            > *"L'ATS Analyzer est un game-changer. Mes lettres passent maintenant 
            > tous les filtres automatiques. ROI immédiat !"*
            > 
            > **Thomas R.** - Reconversion Finance → Startup
            """)
        
        # CTA Principal optimisé
        st.markdown("---")
        
        col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
        
        with col_cta2:
            if st.button(
                "🚀 COMMENCER MON ESSAI PREMIUM", 
                use_container_width=True, 
                type="primary",
                help="Garantie satisfait ou remboursé 30 jours"
            ):
                st.balloons()
                st.success("🎉 Redirection vers le paiement sécurisé...")
                self._track_conversion_event("premium_cta_clicked")
                
                # Formulaire de contact rapide
                st.markdown("### 📧 Finaliser votre abonnement")
                
                with st.form("premium_signup"):
                    email = st.text_input("Email professionnel", placeholder="votre.email@exemple.com")
                    nom = st.text_input("Nom complet", placeholder="Prénom Nom")
                    secteur = st.selectbox(
                        "Secteur de reconversion", 
                        ["Tech/IT", "Marketing/Communication", "Finance", "RH", "Santé", "Éducation", "Autre"]
                    )
                    
                    submitted = st.form_submit_button("💳 Payer 19€/mois", use_container_width=True)
                    
                    if submitted:
                        if email and nom:
                            st.success(f"✅ Merci {nom} ! Votre demande Premium a été envoyée.")
                            st.info("📧 Vous recevrez un lien de paiement sécurisé par email sous 5 minutes.")
                            self._track_conversion_event("premium_form_submitted", {"email": email, "secteur": secteur})
                        else:
                            st.error("⚠️ Veuillez remplir tous les champs")
        
        # Garanties et sécurité
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <p><strong>🛡️ Garanties Premium</strong></p>
            <p>✅ Satisfait ou remboursé 30 jours | 🔒 Paiement sécurisé Stripe | 📱 Annulation en 1 clic</p>
            <p><em>Rejoignez 2,847+ professionnels qui ont déjà transformé leur reconversion</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        # FAQ rapide
        with st.expander("❓ Questions fréquentes"):
            st.markdown("""
            **Q: Puis-je annuler à tout moment ?**  
            R: Oui, annulation en 1 clic depuis votre profil. Aucun engagement.
            
            **Q: Que se passe-t-il si je ne suis pas satisfait ?**  
            R: Garantie remboursement intégral sous 30 jours, sans questions.
            
            **Q: Mes données sont-elles sécurisées ?**  
            R: 100% RGPD compliant. Données chiffrées et supprimées à la demande.
            
            **Q: Support technique inclus ?**  
            R: Oui, support prioritaire 24/7 par email et chat.
            """)

    def _track_conversion_event(self, event_name: str, properties: Optional[dict] = None):
        """Track conversion events pour analytics"""
        try:
            from core.services.analytics_service import AnalyticsService
            
            analytics = AnalyticsService()
            user_id = st.session_state.get('user_id', 'anonymous')
            user_tier = st.session_state.get('user_tier', 'free')
            
            analytics.track_conversion_funnel(
                step=event_name,
                user_id=user_id,
                user_tier=user_tier,
                source="premium_page",
                properties=properties
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Analytics tracking failed: {e}")
