"""
Faux client Gemini pour le développement et les tests.
"""
import time
import random
from typing import Optional

from core.entities.letter import UserTier
from shared.interfaces.ai_interface import AIServiceInterface

class MockGeminiClient(AIServiceInterface):
    """
    Un faux client Gemini qui simule les réponses de l'API
    pour un développement rapide et sans coût.
    """
    
    def __init__(self):
        """Initialise le faux client."""
        print("--- INITIALIZING MOCK GEMINI CLIENT ---")

    def generate_content(
        self,
        prompt: str,
        user_tier: UserTier,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Simule la génération de contenu en retournant une réponse pré-écrite
        basée sur le type de prompt.
        """
        # Simule une latence réseau réaliste
        time.sleep(random.uniform(0.5, 1.5))

        # Détecte le type de prompt pour retourner une réponse adaptée
        if "Suggérer compétences transférables" in prompt:
            return self._mock_skills_suggestion()
        elif "Génère une lettre de motivation" in prompt:
            return self._mock_letter_generation()
        else:
            return self._default_mock_response()

    def _mock_skills_suggestion(self) -> str:
        """Retourne une suggestion de compétences pré-écrite."""
        return """Voici quelques compétences transférables clés :

- **Gestion de Projet :** Votre expérience dans la planification et le suivi de campagnes marketing se traduit directement par la gestion de projets de développement, en respectant les délais et les budgets.
- **Analyse de Données :** L'analyse des performances des campagnes (KPIs) est très similaire à l'analyse des métriques d'utilisation des logiciels pour identifier les points d'amélioration.
- **Communication Stratégique :** La capacité à présenter des idées complexes à des clients ou à des équipes internes est essentielle pour communiquer avec les parties prenantes d'un projet technique.
- **Veille Technologique :** Votre habitude de surveiller les tendances du marché est un atout pour rester à jour sur les nouvelles technologies et les frameworks en développement.
"""

    def _mock_letter_generation(self) -> str:
        """Retourne un modèle de lettre de motivation pré-écrit."""
        return """[Votre Nom]
[Votre Adresse]
[Votre Téléphone]
[Votre Email]

[Date]

[Nom du Recruteur]
[Titre du Recruteur]
[Nom de l'Entreprise]
[Adresse de l'Entreprise]

**Objet : Candidature au poste de [Titre du Poste] - Simulation**

Madame, Monsieur,

Ceci est une lettre de motivation générée par le **Mock API Client** de Phoenix Letters. Elle sert à tester l'interface utilisateur sans faire de véritables appels à l'API Gemini.

Passionné par les défis techniques et fort d'une expérience significative acquise lors de mon parcours, je suis convaincu que mes compétences correspondent parfaitement au profil que vous recherchez.

Mon CV ci-joint détaille mon parcours, mais je souhaitais souligner ma capacité à m'adapter rapidement et à maîtriser de nouveaux outils, une compétence essentielle dans un secteur en constante évolution.

Je serais ravi de pouvoir échanger avec vous plus en détail sur ma motivation et mes compétences lors d'un entretien.

Dans l'attente de votre retour, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Cordialement,

[Votre Nom]
"""

    def _default_mock_response(self) -> str:
        """Réponse par défaut si le prompt n'est pas reconnu."""
        return "Réponse simulée par le MockGeminiClient."
