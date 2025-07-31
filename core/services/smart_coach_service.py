"""Service Smart Coach - Feedback IA temps réel."""
import logging
import re
from typing import Dict, List, Optional
from dataclasses import asdict

from core.entities.letter import SmartCoachFeedback, UserTier
from shared.interfaces.ai_interface import AIServiceInterface
from infrastructure.security.input_validator import InputValidator

logger = logging.getLogger(__name__)

class SmartCoachService:
    """Service de feedback IA en temps réel sur la qualité des lettres."""
    
    def __init__(self, ai_client: AIServiceInterface, input_validator: InputValidator):
        self.ai_client = ai_client
        self.input_validator = input_validator
        
        # Critères d'évaluation avec poids
        self.evaluation_criteria = {
            "clarity": {
                "weight": 0.25,
                "indicators": ["phrases courtes", "vocabulaire simple", "structure logique"]
            },
            "impact": {
                "weight": 0.30,
                "indicators": ["verbes d'action", "résultats quantifiés", "accomplissements"]
            },
            "personalization": {
                "weight": 0.25,
                "indicators": ["nom entreprise", "poste spécifique", "compétences ciblées"]
            },
            "tone": {
                "weight": 0.20,
                "indicators": ["politesse", "professionnalisme", "enthousiasme"]
            }
        }
        
        # Patterns problématiques
        self.critical_issues_patterns = {
            "repetition": r'\b(\w+)\b(?:\W+\1\b){2,}',
            "passive_voice": r'\b(est|sont|était|étaient)\s+\w+é[es]?\b',
            "weak_verbs": r'\b(faire|avoir|être|il y a)\b',
            "generic_phrases": [
                "je suis motivé", "je souhaite", "j'aimerais", "je pense que",
                "suite à votre annonce", "candidature spontanée"
            ]
        }

    def analyze_letter_real_time(self, letter_content: str, 
                               job_title: Optional[str] = None,
                               company_name: Optional[str] = None,
                               user_tier: UserTier = UserTier.FREE) -> SmartCoachFeedback:
        """
        Analyse en temps réel d'une lettre de motivation.
        
        Args:
            letter_content: Contenu de la lettre
            job_title: Titre du poste (optionnel)
            company_name: Nom de l'entreprise (optionnel)
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            SmartCoachFeedback: Feedback détaillé
        """
        if user_tier == UserTier.FREE:
            logger.info("Smart Coach is a premium feature. Returning default for Free user.")
            return self._get_fallback_feedback(letter_content, is_premium_feature=True)

        try:
            logger.info("Starting real-time letter analysis")
            
            # Validation et nettoyage
            clean_content = self.input_validator.sanitize_text_input(letter_content)
            
            # Analyses individuelles
            clarity_analysis = self._analyze_clarity(clean_content)
            impact_analysis = self._analyze_impact(clean_content)
            personalization_analysis = self._analyze_personalization(clean_content, job_title, company_name)
            tone_analysis = self._analyze_tone(clean_content)
            
            # Détection des problèmes critiques
            critical_issues = self._detect_critical_issues(clean_content)
            
            # Points positifs
            positive_points = self._identify_positive_points(clean_content)
            
            # Suggestions spécifiques
            specific_suggestions = self._generate_specific_suggestions(
                clarity_analysis, impact_analysis, personalization_analysis, tone_analysis
            )
            
            # Score global
            overall_score = self._calculate_overall_score(
                clarity_analysis, impact_analysis, personalization_analysis, tone_analysis
            )
            
            # Étapes suivantes
            next_steps = self._generate_next_steps(overall_score, critical_issues)
            
            # Temps de lecture estimé
            estimated_read_time = self._estimate_read_time(clean_content)
            
            feedback = SmartCoachFeedback(
                letter_content=clean_content,
                overall_score=overall_score,
                clarity_score=clarity_analysis["score"],
                impact_score=impact_analysis["score"],
                personalization_score=personalization_analysis["score"],
                professional_tone_score=tone_analysis["score"],
                specific_suggestions=specific_suggestions,
                positive_points=positive_points,
                critical_issues=critical_issues,
                next_steps=next_steps,
                estimated_read_time=estimated_read_time
            )
            
            logger.info(f"Letter analysis completed - Overall score: {overall_score}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error in real-time analysis: {e}")
            return self._get_fallback_feedback(letter_content)

    def _analyze_clarity(self, content: str) -> Dict:
        """Analyse la clarté du contenu."""
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Phrases courtes = plus clair
        clarity_score = max(0, 100 - (avg_sentence_length - 15) * 2)
        clarity_score = min(100, clarity_score)
        
        issues = []
        if avg_sentence_length > 25:
            issues.append("Phrases trop longues détectées")
        
        # Détection de mots complexes
        complex_words = self._count_complex_words(content)
        if complex_words > len(content.split()) * 0.1:
            issues.append("Vocabulaire trop complexe")
            clarity_score -= 10
        
        return {
            "score": max(0, clarity_score),
            "avg_sentence_length": avg_sentence_length,
            "issues": issues,
            "suggestions": self._get_clarity_suggestions(avg_sentence_length, complex_words)
        }

    def _analyze_impact(self, content: str) -> Dict:
        """Analyse l'impact et la force du contenu."""
        words = content.lower().split()
        
        # Verbes d'action forts
        action_verbs = [
            "développé", "créé", "optimisé", "amélioré", "dirigé", "géré", "lancé",
            "réalisé", "conçu", "coordonné", "formé", "négocié", "résolu"
        ]
        action_verb_count = sum(1 for word in words if any(verb in word for verb in action_verbs))
        
        # Résultats quantifiés
        quantified_results = len(re.findall(r'\d+%|\d+€|\d+\s*(millions?|milliers?)', content))
        
        # Score d'impact basé sur les verbes d'action et quantifications
        impact_score = (action_verb_count * 10) + (quantified_results * 15)
        impact_score = min(100, impact_score)
        
        return {
            "score": impact_score,
            "action_verbs_found": action_verb_count,
            "quantified_results": quantified_results,
            "suggestions": self._get_impact_suggestions(action_verb_count, quantified_results)
        }

    def _analyze_personalization(self, content: str, job_title: Optional[str], 
                                company_name: Optional[str]) -> Dict:
        """Analyse le niveau de personnalisation."""
        score = 50  # Score de base
        
        # Vérification nom entreprise
        if company_name and company_name.lower() in content.lower():
            score += 20
        else:
            score -= 10
        
        # Vérification titre du poste
        if job_title and job_title.lower() in content.lower():
            score += 15
        
        # Détection de phrases génériques
        generic_count = sum(1 for phrase in self.critical_issues_patterns["generic_phrases"] 
                          if phrase in content.lower())
        score -= generic_count * 5
        
        # Spécificité du vocabulaire
        if "votre entreprise" in content.lower() and company_name:
            score += 10
        
        return {
            "score": max(0, min(100, score)),
            "company_mentioned": company_name and company_name.lower() in content.lower(),
            "job_title_mentioned": job_title and job_title.lower() in content.lower(),
            "generic_phrases_count": generic_count,
            "suggestions": self._get_personalization_suggestions(company_name, job_title, generic_count)
        }

    def _analyze_tone(self, content: str) -> Dict:
        """Analyse le ton professionnel."""
        # Formules de politesse
        politeness_indicators = ["madame", "monsieur", "cordialement", "respectueusement", "veuillez"]
        politeness_score = sum(1 for indicator in politeness_indicators if indicator in content.lower()) * 10
        
        # Enthousiasme approprié
        enthusiasm_indicators = ["enthousiaste", "motivé", "passionné", "intéressé"]
        enthusiasm_score = sum(1 for indicator in enthusiasm_indicators if indicator in content.lower()) * 5
        
        # Professionnalisme
        professional_tone = not any(word in content.lower() for word in ["salut", "bonjour", "sympa", "cool"])
        professional_score = 30 if professional_tone else 0
        
        total_score = min(100, politeness_score + enthusiasm_score + professional_score)
        
        return {
            "score": total_score,
            "politeness_score": min(50, politeness_score),
            "enthusiasm_score": min(25, enthusiasm_score),
            "professional_score": professional_score,
            "suggestions": self._get_tone_suggestions(politeness_score, enthusiasm_score, professional_score)
        }

    def _detect_critical_issues(self, content: str) -> List[str]:
        """Détecte les problèmes critiques."""
        issues = []
        
        # Répétitions
        if re.search(self.critical_issues_patterns["repetition"], content, re.IGNORECASE):
            issues.append("Répétitions détectées - variez votre vocabulaire")
        
        # Voix passive excessive
        passive_matches = len(re.findall(self.critical_issues_patterns["passive_voice"], content, re.IGNORECASE))
        if passive_matches > 3:
            issues.append("Trop de voix passive - utilisez la voix active")
        
        # Verbes faibles
        weak_verb_matches = len(re.findall(self.critical_issues_patterns["weak_verbs"], content, re.IGNORECASE))
        if weak_verb_matches > 5:
            issues.append("Verbes faibles détectés - utilisez des verbes d'action")
        
        # Longueur inappropriée
        word_count = len(content.split())
        if word_count < 200:
            issues.append("Lettre trop courte - développez vos arguments")
        elif word_count > 500:
            issues.append("Lettre trop longue - condensez votre message")
        
        # Fautes potentielles (détection basique)
        if content.count('  ') > 3:  # Espaces doubles
            issues.append("Espaces doubles détectés - vérifiez la mise en forme")
        
        return issues

    def _identify_positive_points(self, content: str) -> List[str]:
        """Identifie les points positifs de la lettre."""
        positive_points = []
        
        # Structure claire
        if content.count('\n\n') >= 2:
            positive_points.append("Structure claire avec paragraphes distincts")
        
        # Formules de politesse
        if any(formula in content.lower() for formula in ["madame", "monsieur", "cordialement"]):
            positive_points.append("Formules de politesse appropriées")
        
        # Résultats quantifiés
        if re.search(r'\d+%|\d+€|\d+\s*ans?', content):
            positive_points.append("Résultats quantifiés mentionnés")
        
        # Longueur appropriée
        word_count = len(content.split())
        if 250 <= word_count <= 400:
            positive_points.append("Longueur appropriée pour une lettre de motivation")
        
        return positive_points

    def _generate_specific_suggestions(self, clarity: Dict, impact: Dict, 
                                     personalization: Dict, tone: Dict) -> List[Dict[str, str]]:
        """Génère des suggestions spécifiques hiérarchisées."""
        suggestions = []
        
        # Suggestions critiques (priorité haute)
        if clarity["score"] < 60:
            suggestions.append({
                "type": "improvement",
                "text": "Simplifiez vos phrases - visez 15-20 mots par phrase maximum",
                "priority": "high"
            })
        
        if impact["score"] < 50:
            suggestions.append({
                "type": "improvement", 
                "text": "Ajoutez des verbes d'action forts et quantifiez vos résultats",
                "priority": "high"
            })
        
        # Suggestions importantes (priorité moyenne)
        if personalization["score"] < 70:
            suggestions.append({
                "type": "improvement",
                "text": "Personnalisez davantage en mentionnant l'entreprise et ses spécificités",
                "priority": "medium"
            })
        
        if tone["score"] < 60:
            suggestions.append({
                "type": "improvement",
                "text": "Renforcez le ton professionnel avec des formules appropriées",
                "priority": "medium"
            })
        
        # Suggestions d'optimisation (priorité basse)
        suggestions.append({
            "type": "optimization",
            "text": "Relisez pour éliminer les répétitions et varier le vocabulaire",
            "priority": "low"
        })
        
        return suggestions[:5]  # Limiter à 5 suggestions

    def _calculate_overall_score(self, clarity: Dict, impact: Dict, 
                               personalization: Dict, tone: Dict) -> float:
        """Calcule le score global pondéré."""
        scores = [
            clarity["score"] * self.evaluation_criteria["clarity"]["weight"],
            impact["score"] * self.evaluation_criteria["impact"]["weight"],
            personalization["score"] * self.evaluation_criteria["personalization"]["weight"],
            tone["score"] * self.evaluation_criteria["tone"]["weight"]
        ]
        return round(sum(scores), 1)

    def _generate_next_steps(self, overall_score: float, critical_issues: List[str]) -> List[str]:
        """Génère les prochaines étapes recommandées."""
        next_steps = []
        
        if overall_score < 50:
            next_steps.append("Révision majeure recommandée - reprenez la structure générale")
        elif overall_score < 70:
            next_steps.append("Améliorations ciblées nécessaires - focus sur les points faibles")
        else:
            next_steps.append("Finitions et optimisations - votre lettre est sur la bonne voie")
        
        if critical_issues:
            next_steps.append("Corrigez les problèmes critiques identifiés en priorité")
        
        next_steps.append("Relecture finale recommandée avant envoi")
        
        return next_steps[:3]

    def _estimate_read_time(self, content: str) -> int:
        """Estime le temps de lecture en secondes (250 mots/minute)."""
        word_count = len(content.split())
        return int((word_count / 250) * 60)

    def _count_complex_words(self, content: str) -> int:
        """Compte les mots complexes (plus de 8 lettres)."""
        words = re.findall(r'\b\w+\b', content.lower())
        return sum(1 for word in words if len(word) > 8)

    def _get_clarity_suggestions(self, avg_length: float, complex_words: int) -> List[str]:
        """Suggestions pour améliorer la clarté."""
        suggestions = []
        if avg_length > 20:
            suggestions.append("Divisez les phrases longues en phrases plus courtes")
        if complex_words > 10:
            suggestions.append("Simplifiez le vocabulaire technique")
        return suggestions

    def _get_impact_suggestions(self, action_verbs: int, quantified: int) -> List[str]:
        """Suggestions pour améliorer l'impact."""
        suggestions = []
        if action_verbs < 3:
            suggestions.append("Utilisez plus de verbes d'action forts")
        if quantified < 2:
            suggestions.append("Quantifiez vos accomplissements avec des chiffres")
        return suggestions

    def _get_personalization_suggestions(self, company: Optional[str], 
                                       job_title: Optional[str], generic_count: int) -> List[str]:
        """Suggestions pour améliorer la personnalisation."""
        suggestions = []
        if company and not company.lower():
            suggestions.append("Mentionnez le nom de l'entreprise")
        if generic_count > 2:
            suggestions.append("Éliminez les phrases génériques")
        return suggestions

    def _get_tone_suggestions(self, politeness: int, enthusiasm: int, professional: int) -> List[str]:
        """Suggestions pour améliorer le ton."""
        suggestions = []
        if politeness < 20:
            suggestions.append("Ajoutez des formules de politesse appropriées")
        if enthusiasm < 10:
            suggestions.append("Montrez votre motivation et votre intérêt")
        if professional < 20:
            suggestions.append("Maintenez un ton professionnel")
        return suggestions

    def _get_fallback_feedback(self, content: str, is_premium_feature: bool = False) -> SmartCoachFeedback:
        """Feedback de secours en cas d'erreur."""
        if is_premium_feature:
            return SmartCoachFeedback(
                letter_content=content,
                overall_score=0.0,
                clarity_score=0.0,
                impact_score=0.0,
                personalization_score=0.0,
                professional_tone_score=0.0,
                specific_suggestions=[{
                    "type": "premium",
                    "text": "Cette fonctionnalité est réservée aux utilisateurs Premium. Passez Premium pour débloquer le Smart Coach.",
                    "priority": "high"
                }],
                positive_points=["Fonctionnalité Premium"],
                critical_issues=["Accès Premium requis"],
                next_steps=["Passez Premium pour une analyse complète"],
                estimated_read_time=0
            )
        return SmartCoachFeedback(
            letter_content=content,
            overall_score=50.0,
            clarity_score=50.0,
            impact_score=50.0,
            personalization_score=50.0,
            professional_tone_score=50.0,
            specific_suggestions=[{
                "type": "error",
                "text": "Analyse temporairement indisponible - réessayez",
                "priority": "medium"
            }],
            positive_points=["Lettre soumise pour analyse"],
            critical_issues=["Service d'analyse temporairement indisponible"],
            next_steps=["Réessayez l'analyse dans quelques instants"],
            estimated_read_time=60
        )