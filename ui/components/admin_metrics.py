"""Composant métriques admin pour suivi conversions."""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any
from core.services.analytics_service import AnalyticsService


class AdminMetrics:
    """Dashboard métriques pour admins/développeurs."""
    
    def __init__(self):
        self.analytics = AnalyticsService()
    
    def render_conversion_metrics(self) -> None:
        """Affiche métriques de conversion dans sidebar."""
        
        # Vérifier si admin/développeur
        if not self._is_admin_user():
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Métriques Admin")
        
        # Métriques temps réel (mock data pour démo)
        metrics = self._get_demo_metrics()
        
        # KPIs principaux
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("Conv. Rate", f"{metrics['conversion_rate']:.1f}%", 
                     delta=f"+{metrics['conv_delta']:.1f}%")
        
        with col2:
            st.metric("Free Users", metrics['free_users'], 
                     delta=f"+{metrics['free_delta']}")
        
        # Détails expandable
        with st.sidebar.expander("📈 Détails"):
            st.markdown(f"""
            **Aujourd'hui:**
            - Premium CTA clicks: {metrics['cta_clicks']}
            - Form submissions: {metrics['form_submits']}
            - Page Premium vues: {metrics['premium_views']}
            
            **Cette semaine:**
            - Lettres générées: {metrics['letters_generated']}
            - Limites atteintes: {metrics['limits_reached']}
            - Upgrades Premium: {metrics['upgrades']}
            """)
        
        # Actions admin rapides
        if st.sidebar.button("🔄 Refresh Metrics"):
            st.rerun()
        
        if st.sidebar.button("📋 Export Data"):
            self._export_metrics_data(metrics)
    
    def _is_admin_user(self) -> bool:
        """Vérifie si utilisateur est admin."""
        user_id = st.session_state.get('user_id', '')
        admin_users = ['admin', 'dev', 'phoenix_admin']  # IDs admin
        
        return (
            user_id in admin_users or 
            st.session_state.get('is_admin', False) or
            st.session_state.get('user_tier') == 'admin'
        )
    
    def _get_demo_metrics(self) -> Dict[str, Any]:
        """Génère métriques démo pour développement."""
        import random
        
        # Simulation métriques réalistes
        base_conversion = 12.5
        daily_variation = random.uniform(-2.0, 3.0)
        
        return {
            'conversion_rate': base_conversion + daily_variation,
            'conv_delta': daily_variation,
            'free_users': random.randint(45, 78),
            'free_delta': random.randint(-5, 12),
            'cta_clicks': random.randint(15, 35),
            'form_submits': random.randint(3, 8),
            'premium_views': random.randint(25, 55),
            'letters_generated': random.randint(120, 200),
            'limits_reached': random.randint(25, 45),
            'upgrades': random.randint(2, 7)
        }
    
    def _export_metrics_data(self, metrics: Dict[str, Any]) -> None:
        """Exporte données métriques."""
        import json
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'session_data': {
                'user_count': len(st.session_state),
                'active_features': self._get_active_features()
            }
        }
        
        # Simulation export
        st.sidebar.success("📊 Données exportées vers logs")
        st.sidebar.json(export_data)
    
    def _get_active_features(self) -> List[str]:
        """Liste des fonctionnalités utilisées dans la session."""
        features = []
        
        if st.session_state.get('mirror_match_used'):
            features.append('mirror_match')
        if st.session_state.get('ats_analyzer_used'):
            features.append('ats_analyzer')
        if st.session_state.get('smart_coach_used'):
            features.append('smart_coach')
        if st.session_state.get('trajectory_builder_used'):
            features.append('trajectory_builder')
        
        return features
    
    def log_feature_usage(self, feature_name: str, user_tier: str) -> None:
        """Log utilisation fonctionnalité pour métriques."""
        user_id = st.session_state.get('user_id', 'anonymous')
        
        # Track avec analytics service
        self.analytics.track_feature_usage(
            feature_name=feature_name,
            user_id=user_id,
            user_tier=user_tier,
            action="used" if user_tier == "premium" else "blocked"
        )
        
        # Marquer dans session pour admin metrics
        st.session_state[f'{feature_name}_used'] = True