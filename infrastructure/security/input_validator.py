"""Service de validation d'entrée sécurisé."""
import logging

from core.entities.letter import GenerationRequest, ToneType
from shared.exceptions.specific_exceptions import ValidationError

logger = logging.getLogger(__name__)

class InputValidator:
    """Valide et nettoie les entrées utilisateur pour prévenir les vulnérabilités."""
    
    def validate_generation_request(self, request: GenerationRequest) -> None:
        """Valide une requête de génération de lettre.
        Args:
            request (GenerationRequest): La requête de génération à valider.
        Raises:
            ValidationError: Si la requête est invalide.
        """
        if not request.job_title or len(request.job_title) < 3:
            raise ValidationError("Le titre du poste est requis et doit contenir au moins 3 caractères.")
        if not request.company_name or len(request.company_name) < 3:
            raise ValidationError("Le nom de l'entreprise est requis et doit contenir au moins 3 caractères.")
        if not request.cv_content or len(request.cv_content) < 50:
            raise ValidationError("Le contenu du CV est requis et doit contenir au moins 50 caractères.")
        if not request.job_offer_content or len(request.job_offer_content) < 50:
            raise ValidationError("Le contenu de l'offre d'emploi est requis et doit contenir au moins 50 caractères.")
        if request.is_career_change and (not request.transferable_skills or len(request.transferable_skills) < 20):
            raise ValidationError("Les compétences transférables sont requises pour une reconversion et doivent contenir au moins 20 caractères.")
        if not request.tone:
            raise ValidationError("Le ton de la lettre est requis.")
        
        logger.info("Generation request validated successfully.")

    def validate_file_content(self, content: bytes, file_extension: str) -> None:
        """Valide le contenu d'un fichier uploadé avec sécurité renforcée.

        Args:
            content (bytes): Contenu binaire du fichier.
            file_extension (str): Extension du fichier (ex: 'pdf', 'txt').

        Raises:
            ValueError: Si le contenu est invalide ou malveillant.
        """
        # Validation de la taille (protection DoS)
        max_size = 10 * 1024 * 1024  # 10MB max
        if len(content) > max_size:
            logger.warning(f"File too large: {len(content)} bytes")
            raise ValueError("Fichier trop volumineux (max 10MB).")
        
        if file_extension == 'txt':
            try:
                decoded_content = content.decode('utf-8')
                # Détection avancée de contenu malveillant
                malicious_patterns = [
                    '<script', '</script>', '<iframe', 'javascript:', 'vbscript:',
                    'data:text/html', '<object', '<embed', '<form', 'eval(',
                    'document.write', 'window.location', 'document.location'
                ]
                content_lower = decoded_content.lower()
                for pattern in malicious_patterns:
                    if pattern in content_lower:
                        logger.warning(f"Malicious pattern detected: {pattern}")
                        raise ValueError(f"Contenu potentiellement malveillant détecté: {pattern}")
                        
                # Vérification encodage et caractères suspects
                if len([c for c in decoded_content if ord(c) > 127]) > len(decoded_content) * 0.3:
                    logger.warning("High ratio of non-ASCII characters detected")
                    raise ValueError("Fichier TXT contient trop de caractères non-ASCII.")
                    
            except UnicodeDecodeError:
                logger.warning("Could not decode TXT file as UTF-8.")
                raise ValueError("Fichier TXT invalide (encodage non UTF-8).")
                
        elif file_extension == 'pdf':
            # Validation PDF robuste
            if not content.startswith(b'%PDF'):
                logger.warning("Invalid PDF magic number.")
                raise ValueError("Fichier PDF invalide (signature manquante).")
            
            # Vérification version PDF supportée
            pdf_version = content[5:8]
            supported_versions = [b'1.3', b'1.4', b'1.5', b'1.6', b'1.7', b'2.0']
            if pdf_version not in supported_versions:
                logger.warning(f"Unsupported PDF version: {pdf_version}")
                raise ValueError(f"Version PDF non supportée: {pdf_version.decode()}")
            
            # Détection patterns suspects dans PDF
            suspicious_pdf_patterns = [
                b'/JavaScript', b'/JS', b'/Launch', b'/GoToR', b'/GoToE',
                b'/EmbeddedFile', b'/XFA', b'/RichMedia', b'/3D'
            ]
            for pattern in suspicious_pdf_patterns:
                if pattern in content:
                    logger.warning(f"Suspicious PDF pattern detected: {pattern}")
                    raise ValueError(f"PDF contient des éléments potentiellement dangereux: {pattern.decode()}")
            
            # Vérification structure PDF basique
            if b'%%EOF' not in content[-1024:]:
                logger.warning("PDF missing EOF marker")
                raise ValueError("Structure PDF invalide (marqueur EOF manquant).")
                
        else:
            logger.warning(f"Unsupported file extension for content validation: {file_extension}")
            raise ValueError(f"Type de fichier non supporté pour la validation de contenu: {file_extension}")

    def sanitize_text_input(self, text: str) -> str:
        """Nettoie une chaîne de texte pour prévenir les injections.
        Args:
            text (str): Chaîne de texte à nettoyer.
        Returns:
            str: Chaîne de texte nettoyée.
        """
        # Exemple de nettoyage basique (à étendre)
        return text.replace('<', '&lt;').replace('>', '&gt;').strip()

    def validate_email(self, email: str) -> bool:
        """Valide le format d'une adresse email.
        Args:
            email (str): Adresse email à valider.
        Returns:
            bool: True si l'email est valide, False sinon.
        """
        import re
        return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None
