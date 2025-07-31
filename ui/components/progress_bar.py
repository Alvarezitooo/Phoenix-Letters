"""Composant d'indicateur de progression Streamlit."""
import streamlit as st

class ProgressIndicator:
    """Affiche un indicateur de progression personnalisable."""
    
    def render(self, value: float, label: str = "") -> None:
        """Affiche la barre de progression."
        Args:
            value: Valeur de la progression (entre 0 et 100).
            label: Texte à afficher au-dessus de la barre de progression.
        """
        st.progress(value / 100, text=label)