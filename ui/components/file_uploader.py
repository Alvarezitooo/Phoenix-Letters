"""Composant de téléchargement de fichiers sécurisé."""
import streamlit as st
from typing import Optional, List, Callable
import hashlib
import logging

from config.settings import Settings
from shared.exceptions.specific_exceptions import FileValidationError
from infrastructure.security.input_validator import InputValidator

from shared.interfaces.validation_interface import ValidationServiceInterface
from config.settings import Settings

logger = logging.getLogger(__name__)

class SecureFileUploader:
    """Composant de téléchargement de fichiers avec validation sécurisée."""
    
    def __init__(self, input_validator: ValidationServiceInterface, settings: Settings):
        self.input_validator = input_validator
        self.settings = settings
        logger.info("SecureFileUploader initialized")
    
    def render(
        self,
        label: str,
        accepted_types: List[str],
        key: str,
        max_size: Optional[int] = None,
        help_text: Optional[str] = None,
        on_upload: Optional[Callable] = None
    ) -> Optional[bytes]:
        """
        Affiche un composant de téléchargement sécurisé.
        
        Args:
            label: Label du composant
            accepted_types: Types de fichiers acceptés
            key: Clé unique pour le composant
            max_size: Taille maximale en bytes
            help_text: Texte d'aide
            on_upload: Callback appelé après upload
            
        Returns:
            Optional[bytes]: Contenu du fichier ou None
            
        Raises:
            FileValidationError: En cas de fichier invalide
        """
        max_size = max_size or self.settings.max_file_size
        
        # Interface utilisateur
        uploaded_file = st.file_uploader(
            label,
            type=accepted_types,
            key=key,
            help=help_text or f"Formats acceptés: {', '.join(accepted_types).upper()}. Taille max: {max_size // (1024*1024)}MB"
        )
        
        if uploaded_file is None:
            return None
        
        try:
            # Validation sécurisée
            file_content = self._validate_and_process_file(
                uploaded_file, 
                accepted_types, 
                max_size
            )
            
            # Feedback utilisateur
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            st.success(f"✅ {uploaded_file.name} chargé (ID: {file_hash})")
            
            # Callback si défini
            if on_upload:
                on_upload(uploaded_file.name, file_content)
            
            return file_content
            
        except FileValidationError as e:
            st.error(f"❌ Erreur de fichier: {e}")
            logger.warning(f"File validation error for {uploaded_file.name}: {e}")
            return None
        except Exception as e:
            st.error(f"❌ Erreur inattendue lors du traitement du fichier")
            logger.error(f"Unexpected error processing file {uploaded_file.name}: {e}")
            return None
    
    def _validate_and_process_file(
        self, 
        uploaded_file, 
        accepted_types: List[str],
        max_size: int
    ) -> bytes:
        """
        Valide et traite un fichier uploadé.
        
        Args:
            uploaded_file: Fichier uploadé par Streamlit
            accepted_types: Types acceptés
            max_size: Taille maximale
            
        Returns:
            bytes: Contenu validé du fichier
            
        Raises:
            FileValidationError: En cas d'erreur de validation
        """
        # Validation du nom de fichier
        if not uploaded_file.name or len(uploaded_file.name) > 255:
            raise FileValidationError("Nom de fichier invalide")
        
        # Validation de l'extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in accepted_types:
            raise FileValidationError(f"Type de fichier non autorisé: .{file_extension}")
        
        # Lecture du contenu
        file_content = uploaded_file.getvalue()
        
        # Validation de la taille
        if len(file_content) == 0:
            raise FileValidationError("Fichier vide")
        
        if len(file_content) > max_size:
            raise FileValidationError(f"Fichier trop volumineux ({len(file_content) // (1024*1024)}MB > {max_size // (1024*1024)}MB)")
        
        # Validation du contenu avec le service de validation
        self.input_validator.validate_file_content(file_content, file_extension)
        
        return file_content