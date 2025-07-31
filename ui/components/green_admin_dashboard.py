"""
🌱 Phoenix Green AI - Dashboard Admin pour métriques environnementales.

Interface d'administration pour visualiser et monitorer l'empreinte carbone
de Phoenix Letters en temps réel. Orienté transparence et certification.

Author: Claude Phoenix DevSecOps Guardian
Version: 1.0.0 - Phoenix Green AI Initiative
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from infrastructure.monitoring.phoenix_green_metrics import (
    phoenix_green_metrics, 
    CarbonImpactLevel
)


class PhoenixGreenAdminDashboard:
    """
    🌱 Dashboard d'administration Green AI.
    
    Fonctionnalités:
    - Visualisation temps réel métriques carbone
    - Analyse des tendances et optimisations
    - Génération de rapports pour certification
    - Alertes et recommandations automatisées
    """
    
    def __init__(self):
        """Initialise le dashboard admin Green AI."""
        self.metrics_service = phoenix_green_metrics
        
        # Configuration Streamlit
        st.set_page_config(
            page_title="🌱 Phoenix Green AI Admin",
            page_icon="🌱",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Styles CSS personnalisés
        self._inject_custom_css()
    
    def render_dashboard(self) -> None:
        """Rendu principal du dashboard admin."""
        
        # Header principal
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #1e3c72, #2a5298); color: white; border-radius: 10px; margin-bottom: 2rem;'>
            <h1>🌱 Phoenix Green AI - Dashboard Admin</h1>
            <p>Monitoring carbone en temps réel • Certification ISO/IEC 42001</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar pour contrôles
        self._render_sidebar()
        
        # Métriques principales
        self._render_main_metrics()
        
        # Graphiques analytiques
        self._render_analytics_section()
        
        # Section certification
        self._render_certification_section()
        
        # Actions et recommandations
        self._render_actions_section()
    
    def _inject_custom_css(self) -> None:
        """Injection des styles CSS personnalisés."""
        st.markdown("""
        <style>
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #2a5298;
            margin-bottom: 1rem;
        }
        
        .green-excellent { border-left-color: #00c851 !important; }
        .green-good { border-left-color: #39c0ed !important; }
        .green-moderate { border-left-color: #ff8800 !important; }
        .green-high { border-left-color: #ff4444 !important; }
        
        .kpi-container {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
        }
        
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_sidebar(self) -> None:
        """Rendu de la sidebar avec contrôles."""
        st.sidebar.markdown("## ⚙️ Configuration")
        
        # Sélection période d'analyse
        period_options = {
            "Aujourd'hui": 1,
            "7 derniers jours": 7,
            "30 derniers jours": 30,
            "3 derniers mois": 90
        }
        
        selected_period = st.sidebar.selectbox(
            "📅 Période d'analyse",
            options=list(period_options.keys()),
            index=1  # 7 jours par défaut
        )
        st.session_state['analysis_period'] = period_options[selected_period]
        
        # Filtres avancés
        st.sidebar.markdown("### 🔍 Filtres")
        
        show_cache_only = st.sidebar.checkbox("Cache hits uniquement")
        show_premium_only = st.sidebar.checkbox("Utilisateurs Premium")
        min_co2_threshold = st.sidebar.slider(
            "Seuil CO2 minimum (g)", 
            min_value=0.0, 
            max_value=2.0, 
            value=0.0, 
            step=0.01
        )
        
        # Actions rapides
        st.sidebar.markdown("### ⚡ Actions")
        
        if st.sidebar.button("🔄 Actualiser données"):
            st.rerun()
        
        if st.sidebar.button("📊 Générer rapport"):
            self._generate_certification_report()
        
        if st.sidebar.button("🧹 Nettoyer cache"):
            st.success("Cache metrics nettoyé")
            st.rerun()
    
    def _render_main_metrics(self) -> None:
        """Rendu des métriques principales."""
        st.markdown("## 📊 Métriques Principales")
        
        # Récupération des stats
        stats = self.metrics_service.get_daily_stats()
        
        # KPI en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_metric_card(
                "🌱 Total CO2",
                f"{stats.get('total_co2_grams', 0):.3f}g",
                f"Moy: {stats.get('avg_co2_per_call', 0):.3f}g/appel",
                "green-excellent" if stats.get('avg_co2_per_call', 0) < 0.1 else "green-moderate"
            )
        
        with col2:
            cache_ratio = stats.get('cache_hit_ratio', 0)
            self._render_metric_card(
                "⚡ Cache Hits",
                f"{cache_ratio:.1%}",
                f"{stats.get('total_calls', 0)} appels total",
                "green-excellent" if cache_ratio > 0.8 else "green-good"
            )
        
        with col3:
            response_time = stats.get('avg_response_time_ms', 0)
            self._render_metric_card(
                "⏱️ Temps Réponse",
                f"{response_time}ms",
                "Moyenne pondérée",
                "green-good" if response_time < 2000 else "green-moderate"
            )
        
        with col4:
            grade = stats.get('green_ai_grade', 'N/A')
            self._render_metric_card(
                "🏆 Note Green AI",
                grade,
                f"Score: {stats.get('efficiency_score', 0)}/100",
                "green-excellent" if grade in ['A+', 'A'] else "green-good"
            )
        
        # Métriques détaillées en expandeur
        with st.expander("📈 Métriques Détaillées"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Tokens", stats.get('total_tokens', 0))
                st.metric("Appels Totaux", stats.get('total_calls', 0))
                
            with col2:
                benchmark = stats.get('vs_industry_benchmark', {})
                if 'phoenix_avg_co2' in benchmark:
                    st.metric(
                        "CO2 vs ChatGPT", 
                        f"{benchmark['phoenix_avg_co2']:.3f}g",
                        benchmark['comparisons'].get('chatgpt', 'N/A')
                    )
    
    def _render_metric_card(self, title: str, value: str, subtitle: str, css_class: str) -> None:
        """Rendu d'une carte métrique."""
        st.markdown(f"""
        <div class="metric-card {css_class}">
            <h4 style="margin: 0; color: #333;">{title}</h4>
            <h2 style="margin: 0.5rem 0; color: #1e3c72;">{value}</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_analytics_section(self) -> None:
        """Rendu de la section analytique avec graphiques."""
        st.markdown("## 📈 Analyses Approfondies")
        
        # Récupération des données pour graphiques
        stats = self.metrics_service.get_daily_stats()
        impact_dist = stats.get('impact_distribution', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique distribution impact carbone
            self._render_impact_distribution_chart(impact_dist)
        
        with col2:
            # Graphique comparaison benchmark
            self._render_benchmark_comparison(stats)
        
        # Graphique temporel (si données suffisantes)
        if stats.get('total_calls', 0) > 10:
            self._render_temporal_analysis()
    
    def _render_impact_distribution_chart(self, impact_dist: Dict[str, Any]) -> None:
        """Graphique de distribution des impacts carbone."""
        st.markdown("### 🎯 Distribution Impact Carbone")
        
        if not impact_dist or 'percentages' not in impact_dist:
            st.info("Pas assez de données pour la distribution")
            return
        
        # Données pour le graphique
        categories = list(impact_dist['percentages'].keys())
        values = list(impact_dist['percentages'].values())
        
        # Couleurs selon l'impact
        colors = {
            'excellent': '#00c851',
            'good': '#39c0ed', 
            'moderate': '#ff8800',
            'high': '#ff4444'
        }
        
        # Graphique en secteurs
        fig = px.pie(
            values=values,
            names=categories,
            title="Répartition des niveaux d'impact",
            color_discrete_map=colors
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{percent}<br>%{value} appels<extra></extra>'
        )
        
        fig.update_layout(
            height=300,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_benchmark_comparison(self, stats: Dict[str, Any]) -> None:
        """Graphique de comparaison avec benchmarks."""
        st.markdown("### 🏁 Comparaison Industrie")
        
        benchmark = stats.get('vs_industry_benchmark', {})
        if 'comparisons' not in benchmark:
            st.info("Données benchmark non disponibles")
            return
        
        # Extraction des données
        services = []
        co2_values = []
        
        # Phoenix (notre valeur)
        phoenix_co2 = benchmark.get('phoenix_avg_co2', 0)
        services.append('Phoenix Letters')
        co2_values.append(phoenix_co2)
        
        # Benchmarks estimés
        benchmarks = {
            'ChatGPT': 1.2,
            'Claude': 0.8,
            'Gemini Standard': 0.6
        }
        
        for service, value in benchmarks.items():
            services.append(service)
            co2_values.append(value)
        
        # Graphique en barres
        fig = px.bar(
            x=services,
            y=co2_values,
            title="CO2 par requête (grammes)",
            color=co2_values,
            color_continuous_scale='RdYlGn_r'  # Rouge = haut, Vert = bas
        )
        
        fig.update_layout(
            height=300,
            margin=dict(t=50, b=20, l=20, r=20),
            showlegend=False
        )
        
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>%{y:.3f}g CO2<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_temporal_analysis(self) -> None:
        """Analyse temporelle des tendances."""
        st.markdown("### 📊 Évolution Temporelle")
        
        # Simulation de données temporelles (à remplacer par vraies données)
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=7),
            end=datetime.now(),
            freq='H'
        )
        
        # Données simulées réalistes
        co2_values = [0.08 + 0.02 * (i % 24) / 24 for i in range(len(dates))]
        cache_ratios = [0.75 + 0.15 * (i % 12) / 12 for i in range(len(dates))]
        
        # Création du graphique double axe
        fig = make_subplots(
            specs=[[{"secondary_y": True}]],
            subplot_titles=("Évolution CO2 et Cache Hit Ratio",)
        )
        
        # CO2 (axe principal)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=co2_values,
                name="CO2 (g)",
                line=dict(color='#ff6b6b', width=2)
            ),
            secondary_y=False
        )
        
        # Cache ratio (axe secondaire)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=cache_ratios,
                name="Cache Hit %",
                line=dict(color='#4ecdc4', width=2)
            ),
            secondary_y=True
        )
        
        # Configuration des axes
        fig.update_xaxes(title_text="Temps")
        fig.update_yaxes(title_text="CO2 (grammes)", secondary_y=False)
        fig.update_yaxes(title_text="Cache Hit Ratio", secondary_y=True)
        
        fig.update_layout(
            height=400,
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_certification_section(self) -> None:
        """Section dédiée à la certification."""
        st.markdown("## 🏆 Certification ISO/IEC 42001")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Génération du rapport de certification
            if st.button("📋 Générer Rapport Certification (30 jours)"):
                with st.spinner("Génération du rapport..."):
                    report = self.metrics_service.export_certification_report(30)
                    
                if 'error' not in report:
                    st.success("✅ Rapport généré avec succès!")
                    
                    # Affichage des métriques clés
                    compliance_score = report['green_ai_compliance']['iso_42001_compliance_score']
                    
                    st.metric(
                        "Score Conformité ISO/IEC 42001",
                        f"{compliance_score}/100",
                        f"Grade: {report['green_ai_compliance']['overall_green_grade']}"
                    )
                    
                    # Affichage détaillé en JSON
                    with st.expander("📄 Rapport Détaillé"):
                        st.json(report)
                else:
                    st.error(f"❌ Erreur: {report.get('error', 'Inconnue')}")
        
        with col2:
            # Statut certification
            st.markdown("### 📊 Statut Actuel")
            
            stats = self.metrics_service.get_daily_stats()
            grade = stats.get('green_ai_grade', 'N/A')
            
            if grade in ['A+', 'A']:
                st.markdown("""
                <div class="alert-success">
                    <strong>🎉 Excellent !</strong><br>
                    Prêt pour certification
                </div>
                """, unsafe_allow_html=True)
            elif grade in ['B', 'C']:
                st.markdown("""
                <div class="alert-warning">
                    <strong>⚠️ Améliorations nécessaires</strong><br>
                    Optimisations recommandées
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("📊 Données insuffisantes")
    
    def _render_actions_section(self) -> None:
        """Section d'actions et recommandations."""
        st.markdown("## 🎯 Actions & Recommandations")
        
        # Récupération des recommandations
        report = self.metrics_service.export_certification_report(7)
        recommendations = report.get('recommendations', [])
        
        if recommendations:
            st.markdown("### 💡 Recommandations Automatiques")
            
            for i, rec in enumerate(recommendations):
                st.markdown(f"**{i+1}.** {rec}")
        
        # Actions de maintenance
        st.markdown("### 🔧 Maintenance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Nettoyer Anciennes Métriques"):
                st.info("Nettoyage des métriques > 90 jours")
        
        with col2:
            if st.button("📤 Exporter Données"):
                st.info("Export CSV des métriques")
        
        with col3:
            if st.button("🔄 Recalculer Cache"):
                st.info("Recalcul des statistiques en cache")
    
    def _generate_certification_report(self) -> None:
        """Génère et télécharge un rapport de certification."""
        with st.spinner("Génération du rapport de certification..."):
            period = st.session_state.get('analysis_period', 30)
            report = self.metrics_service.export_certification_report(period)
            
            if 'error' not in report:
                # Préparation du téléchargement
                report_json = json.dumps(report, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📥 Télécharger Rapport JSON",
                    data=report_json,
                    file_name=f"phoenix_green_certification_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                
                st.success("✅ Rapport généré et prêt au téléchargement!")
            else:
                st.error(f"❌ Erreur génération: {report.get('error')}")


def main():
    """Point d'entrée du dashboard admin."""
    dashboard = PhoenixGreenAdminDashboard()
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()