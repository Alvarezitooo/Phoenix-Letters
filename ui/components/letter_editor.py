"""Composant d'édition de lettre Streamlit."""
import streamlit as st

class LetterEditor:
    """Permet d'afficher et d'éditer le contenu d'une lettre."""
    
    def render(self, content: str, key: str) -> str:
        """Affiche un éditeur de texte pour la lettre."
        Args:
            content: Contenu initial de la lettre.
            key: Clé unique pour le composant Streamlit.
        Returns:
            str: Contenu édité de la lettre.
        """
        return st.text_area(
            "Contenu de la lettre",
            value=content,
            height=400,
            key=key
        )