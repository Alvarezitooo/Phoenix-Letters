import streamlit as st

class SettingsPage:
    def __init__(self):
        pass

    def render(self):
        st.title("Paramètres de l'Application")
        st.write("Gérez les préférences de votre application ici.")
        st.write("\n**Options disponibles (à venir) :**")
        st.write("- Préférences de langue")
        st.write("- Thème de l'interface")
        st.write("- Gestion des notifications")