"""
Gestionnaire de connexion à la base de données pour Phoenix Letters.
Fournit un pool de connexions asynchrones à PostgreSQL.
"""
import asyncpg
from asyncpg import Pool
from typing import Optional

# from config.settings import Settings

"""
Gestionnaire de connexion à la base de données pour Phoenix Letters.
Fournit un pool de connexions asynchrones à PostgreSQL.
"""
import asyncpg
import logging
from asyncpg import Pool
from typing import Optional
from config.settings import Settings
from shared.exceptions.specific_exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Gère le cycle de vie du pool de connexions à la base de données.
    """
    _pool: Optional[Pool] = None

    def __init__(self, settings: Settings):
        self.settings = settings

    async def initialize(self):
        """Initialise le pool de connexions de manière sécurisée."""
        if not self._pool:
            try:
                dsn = (
                    f"postgres://{self.settings.db_user}:{self.settings.db_password}@"
                    f"{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}"
                )
                self._pool = await asyncpg.create_pool(dsn)
                logger.info("Pool de connexions à la base de données initialisé avec succès.")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du pool de connexions: {e}")
                raise DatabaseError(f"Impossible de se connecter à la base de données: {e}")

    async def close(self):
        """Ferme le pool de connexions."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Pool de connexions à la base de données fermé.")

    def get_pool(self) -> Pool:
        """Retourne le pool de connexions actif."""
        if not self._pool:
            raise DatabaseError("Le pool de connexions n'a pas été initialisé. Appelez d'abord initialize().")
        return self._pool

