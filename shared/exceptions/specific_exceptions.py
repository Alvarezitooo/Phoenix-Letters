"""
Exceptions spécifiques pour l'application Phoenix Letters.
"""

class DatabaseError(Exception):
    """Exception levée pour les erreurs liées à la base de données."""
    pass

class AuthenticationError(Exception):
    """Exception levée pour les erreurs d'authentification."""
    pass

class UserNotFoundError(Exception):
    """Exception levée lorsqu'un utilisateur n'est pas trouvé."""
    pass

class SessionError(Exception):
    """Exception levée pour les erreurs liées à la session."""
    pass

class SecurityError(Exception):
    """Exception levée pour les violations de sécurité."""
    pass

class ValidationError(Exception):
    """Exception levée pour les erreurs de validation des données."""
    pass

class AIServiceError(Exception):
    """Exception levée pour les erreurs liées au service d'IA."""
    pass

class RateLimitError(Exception):
    """Exception levée lorsque la limite de taux d'appels est atteinte."""
    pass

class LetterGenerationError(Exception):
    """Exception levée pour les erreurs lors de la génération de lettres.""" 
    pass

class FileValidationError(Exception):
    """Exception levée pour les erreurs de validation de fichier."""
    pass
