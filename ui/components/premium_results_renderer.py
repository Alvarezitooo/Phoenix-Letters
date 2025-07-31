"""Composant pour l'affichage standardisé des résultats Premium."""
import streamlit as st
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetricCard:
    """Carte métrique standardisée."""
    title: str
    value: str
    delta: Optional[str] = None
    help_text: Optional[str] = None
    icon: str = "📊"


@dataclass
class ResultSection:
    """Section de résultats standardisée."""
    title: str
    content: List[str]
    section_type: str = "info"  # info, success, warning, error


class PremiumResultsRenderer:
    """Renderer standardisé pour les résultats des fonctionnalités Premium."""
    
    def __init__(self):
        """Initialise le renderer avec les styles par défaut."""
        self.primary_color = "#FF6B35"
        self.success_color = "#2ECC71"
        self.warning_color = "#F39C12"
        self.error_color = "#E74C3C"
    
    def render_header(self, title: str, subtitle: str, icon: str = "✨") -> None:
        """Affiche un header standardisé pour les résultats Premium."""
        st.markdown(f"## {icon} {title}")
        st.caption(subtitle)
        st.markdown("---")
    
    def render_metrics_row(self, metrics: List[MetricCard]) -> None:
        """Affiche une rangée de métriques sous forme de cards."""
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                st.metric(
                    label=f"{metric.icon} {metric.title}",
                    value=metric.value,
                    delta=metric.delta,
                    help=metric.help_text
                )
    
    def render_score_gauge(self, score: float, title: str, max_score: float = 100) -> None:
        """Affiche une jauge de score visuelle."""
        # Normalisation du score
        normalized_score = min(max(score / max_score, 0), 1)
        
        # Couleur basée sur le score
        if normalized_score >= 0.8:
            color = self.success_color
            status = "Excellent"
        elif normalized_score >= 0.6:
            color = self.primary_color
            status = "Bon"
        elif normalized_score >= 0.4:
            color = self.warning_color
            status = "Moyen"
        else:
            color = self.error_color
            status = "À améliorer"
        
        # Affichage
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.progress(normalized_score, text=f"{title}: {score:.1f}/{max_score}")
        
        with col2:
            st.markdown(f"**{status}**")
    
    def render_result_sections(self, sections: List[ResultSection]) -> None:
        """Affiche des sections de résultats de manière standardisée."""
        for section in sections:
            if section.section_type == "success":
                with st.container():
                    st.success(f"**{section.title}**")
                    for item in section.content:
                        st.write(f"✅ {item}")
            
            elif section.section_type == "warning":
                with st.container():
                    st.warning(f"**{section.title}**")
                    for item in section.content:
                        st.write(f"⚠️ {item}")
            
            elif section.section_type == "error":
                with st.container():
                    st.error(f"**{section.title}**")
                    for item in section.content:
                        st.write(f"❌ {item}")
            
            else:  # info par défaut
                with st.container():
                    st.info(f"**{section.title}**")
                    for item in section.content:
                        st.write(f"ℹ️ {item}")
            
            st.markdown("---")
    
    def render_keyword_cloud(self, keywords: List[str], title: str = "Mots-clés identifiés") -> None:
        """Affiche un nuage de mots-clés visuel."""
        st.markdown(f"**{title}**")
        
        # Création des badges colorés pour les mots-clés
        keyword_html = ""
        colors = [self.primary_color, self.success_color, self.warning_color, "#3498DB"]
        
        for i, keyword in enumerate(keywords):
            color = colors[i % len(colors)]
            keyword_html += f"""
            <span style="
                background-color: {color}20;
                color: {color};
                padding: 4px 8px;
                margin: 2px;
                border-radius: 12px;
                border: 1px solid {color}40;
                font-size: 0.9em;
                font-weight: 500;
                display: inline-block;
            ">{keyword}</span>
            """
        
        st.markdown(keyword_html, unsafe_allow_html=True)
    
    def render_recommendations_list(self, recommendations: List[str], title: str = "Recommandations") -> None:
        """Affiche une liste de recommandations avec icônes."""
        st.markdown(f"### 🎯 {title}")
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    
    def render_confidence_indicator(self, confidence: float, title: str = "Niveau de confiance") -> None:
        """Affiche un indicateur de confiance."""
        if confidence >= 0.8:
            st.success(f"🎯 **{title}**: {confidence:.0%} - Très fiable")
        elif confidence >= 0.6:
            st.info(f"📊 **{title}**: {confidence:.0%} - Fiable")
        elif confidence >= 0.4:
            st.warning(f"⚠️ **{title}**: {confidence:.0%} - Modéré")
        else:
            st.error(f"🔍 **{title}**: {confidence:.0%} - Peu fiable")
    
    def render_comparison_table(self, data: Dict[str, Any], title: str = "Analyse comparative") -> None:
        """Affiche un tableau de comparaison."""
        st.markdown(f"### 📊 {title}")
        
        # Conversion en format DataFrame-like pour Streamlit
        formatted_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                formatted_data[key.replace('_', ' ').title()] = f"{value:.1f}"
            else:
                formatted_data[key.replace('_', ' ').title()] = str(value)
        
        # Affichage en colonnes pour un rendu plus agréable
        cols = st.columns(min(len(formatted_data), 3))
        items = list(formatted_data.items())
        
        for i, (key, value) in enumerate(items):
            with cols[i % len(cols)]:
                st.metric(label=key, value=value)
    
    def render_action_buttons(self, actions: List[Dict[str, str]]) -> None:
        """Affiche des boutons d'action contextuels."""
        if not actions:
            return
        
        st.markdown("### 🚀 Actions recommandées")
        cols = st.columns(len(actions))
        
        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(
                    action.get('label', 'Action'),
                    key=f"action_{i}",
                    use_container_width=True,
                    type=action.get('type', 'secondary')
                ):
                    if action.get('callback'):
                        action['callback']()
                    else:
                        st.success(f"Action '{action.get('label')}' déclenchée!")