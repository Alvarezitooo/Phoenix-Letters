"""
Gestionnaire de connexion à Supabase pour Phoenix Letters.
Fournit un client Supabase initialisé et prêt à l'emploi.
"""
import logging
from supabase import create_client, Client, ClientOptions
from typing import Optional

from config.settings import Settings
from shared.exceptions.specific_exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Gère le cycle de vie du client Supabase.
    """
    _client: Optional[Client] = None

    def __init__(self, settings: Settings):
        self.settings = settings
        if not self.settings.supabase_url or not self.settings.supabase_key:
            raise DatabaseError("L'URL et la clé Supabase doivent être définies dans la configuration.")
        
        try:
            options = ClientOptions(schema="api")
            self._client = create_client(
                self.settings.supabase_url, 
                self.settings.supabase_key, 
                options=options
            )
            logger.info("Client Supabase initialisé avec succès pour le schéma 'api'.")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Supabase: {e}")
            raise DatabaseError(f"Impossible de créer le client Supabase: {e}")

    def get_client(self) -> Client:
        """Retourne le client Supabase actif."""
        if not self._client:
            raise DatabaseError("Le client Supabase n'a pas été initialisé.")
        return self._client