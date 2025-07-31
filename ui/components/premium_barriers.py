"""Barrières Premium pour fonctionnalités avancées."""
import streamlit as st
from typing import Callable, Any, Optional
from core.entities.letter import UserTier


class PremiumBarrier:
    """Décorateur et composants pour bloquer fonctionnalités Premium."""
    
    @staticmethod
    def require_premium(feature_name: str, description: str = ""):
        """Décorateur pour fonctions nécessitant Premium."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                user_tier = UserTier(st.session_state.get('user_tier', 'free'))
                
                if user_tier != UserTier.PREMIUM:
                    PremiumBarrier.show_feature_lock(feature_name, description)
                    return None
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def show_feature_lock(feature_name: str, description: str = "") -> None:
        """Affiche verrou Premium pour fonctionnalité."""
        
        st.markdown(f"""
        <div style="border: 2px dashed #ffd700; border-radius: 15px; padding: 2rem; 
                    text-align: center; background: linear-gradient(135deg, #fff8dc, #f0f8ff);">
            <h3>🔒 {feature_name} - Fonctionnalité Premium</h3>
            <p style="color: #666; margin: 1rem 0;">{description}</p>
            
            <div style="background: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <p><strong>✨ Débloquez maintenant :</strong></p>
                <p>• {feature_name} + toutes les fonctionnalités Premium</p>
                <p>• Lettres illimitées</p>
                <p>• Support prioritaire 24/7</p>
            </div>
            
            <p style="font-size: 1.5rem; color: #28a745; margin: 0.5rem 0;">
                <span style="text-decoration: line-through; color: #888;">29€</span> 
                <strong>19€/mois</strong>
            </p>
            <p style="color: #ff6b35; font-size: 0.9rem;">🎉 -33% Offre de lancement</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"🚀 Débloquer {feature_name}", 
                        use_container_width=True, 
                        type="primary",
                        key=f"unlock_{feature_name.lower().replace(' ', '_')}"):
                st.switch_page("Offres Premium")


class SmartUpgradePrompts:
    """Prompts intelligents pour upgrade Premium."""
    
    @staticmethod
    def show_usage_milestone(letters_count: int) -> None:
        """Affiche prompt basé sur utilisation."""
        
        if letters_count == 1:
            st.info("""
            🎯 **Première lettre réussie !** Avec Premium, elle aurait été optimisée avec :
            • **Mirror Match** - Analyse culture entreprise  
            • **ATS Analyzer** - Passage filtres automatiques garantis
            """)
            
        elif letters_count == 2:
            st.warning("""
            ⚠️ **Dernière lettre gratuite !** Pour continuer votre reconversion :
            • **Lettres illimitées** dès maintenant
            • **Tous les outils Premium** pour maximiser vos chances
            """)
            
            if st.button("🚀 Continuer en illimité", key="milestone_upgrade"):
                st.switch_page("Offres Premium")
    
    @staticmethod
    def show_competitive_advantage() -> None:
        """Montre avantage concurrentiel Premium."""
        
        with st.expander("💡 Pourquoi Phoenix Letters Premium ?"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **🆚 Autres solutions :**
                • Generic - Pas spécialisé reconversion
                • Cher - 50€+ pour moins de fonctionnalités  
                • Complexe - Interface difficile
                • Limité - Peu d'outils IA
                """)
            
            with col2:
                st.markdown("""
                **✅ Phoenix Letters Premium :**
                • **Spécialisé reconversion** 100%
                • **19€/mois** - Prix imbattable
                • **Interface intuitive** Streamlit
                • **4 outils IA avancés** inclus
                """)
    
    @staticmethod
    def show_time_sensitive_offer() -> None:
        """Affiche offre limitée dans le temps."""
        
        import datetime
        end_date = datetime.date.today() + datetime.timedelta(days=7)
        
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #ff6b35, #ffd700); 
                    color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h4>⏰ OFFRE LIMITÉE - Se termine le {end_date.strftime('%d/%m')}</h4>
            <p>-33% sur Phoenix Letters Premium</p>
            <p><strong>Seulement 19€/mois au lieu de 29€</strong></p>
        </div>
        """, unsafe_allow_html=True)


class ConversionOptimizer:
    """Optimiseur de conversion avec A/B testing."""
    
    @staticmethod
    def get_cta_variant() -> dict:
        """Retourne variant CTA pour A/B test."""
        import random
        
        variants = [
            {
                "text": "🚀 Passer Premium",
                "color": "primary",
                "style": "standard"
            },
            {
                "text": "✨ Débloquer Maintenant", 
                "color": "primary",
                "style": "urgent"
            },
            {
                "text": "🎯 Commencer Premium",
                "color": "primary", 
                "style": "action"
            }
        ]
        
        # Sélection basée sur user_id pour cohérence
        user_id = st.session_state.get('user_id', 'default')
        variant_index = hash(user_id) % len(variants)
        
        return variants[variant_index]
    
    @staticmethod
    def track_cta_performance(variant: dict, clicked: bool) -> None:
        """Track performance CTA pour optimisation."""
        try:
            from core.services.analytics_service import AnalyticsService
            
            analytics = AnalyticsService()
            user_id = st.session_state.get('user_id', 'anonymous')
            
            analytics.track_event(
                event_name="cta_ab_test",
                user_id=user_id,
                user_tier=st.session_state.get('user_tier', 'free'),
                properties={
                    "variant_text": variant["text"],
                    "variant_style": variant["style"], 
                    "clicked": clicked
                }
            )
        except Exception:
            pass  # Fail silently pour ne pas casser l'UX