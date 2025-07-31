"""Service ATS Analyzer - Optimisation pour systèmes de tri automatique."""
import logging
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import asdict

from core.entities.letter import ATSAnalysis, UserTier
from shared.interfaces.ai_interface import AIServiceInterface
from infrastructure.security.input_validator import InputValidator

logger = logging.getLogger(__name__)

class ATSAnalyzerService:
    """Service d'analyse et d'optimisation ATS (Applicant Tracking System)."""
    
    def __init__(self, ai_client: AIServiceInterface, input_validator: InputValidator):
        self.ai_client = ai_client
        self.input_validator = input_validator
        
        # Verbes d'action valorisés par les ATS
        self.strong_action_verbs = {
            "développé", "créé", "optimisé", "amélioré", "dirigé", "géré", "lancé",
            "réalisé", "conçu", "coordonné", "formé", "négocié", "résolu", "établi",
            "implémenté", "supervisé", "planifié", "organisé", "analysé", "évalué",
            "restructuré", "modernisé", "automatisé", "streamliné", "augmenté",
            "réduit", "économisé", "généré", "obtenu", "atteint", "dépassé"
        }
        
        # Mots-clés par secteur souvent recherchés par les ATS
        self.sector_keywords = {
            "tech": {
                "languages": ["python", "java", "javascript", "c++", "sql", "html", "css"],
                "frameworks": ["react", "angular", "vue", "django", "spring", "nodejs"],
                "tools": ["git", "docker", "kubernetes", "jenkins", "aws", "azure"],
                "concepts": ["agile", "scrum", "devops", "ci/cd", "microservices", "api"]
            },
            "marketing": {
                "digital": ["seo", "sem", "google ads", "facebook ads", "analytics"],
                "tools": ["hubspot", "mailchimp", "hootsuite", "canva", "photoshop"],
                "concepts": ["inbound", "content marketing", "lead generation", "crm"],
                "metrics": ["roi", "cac", "ltv", "conversion", "engagement"]
            },
            "finance": {
                "tools": ["excel", "sap", "oracle", "powerbi", "tableau"],
                "concepts": ["budget", "forecast", "variance", "kpi", "roi", "npv"],
                "regulations": ["ifrs", "gaap", "sox", "basel", "mifid"],
                "skills": ["financial modeling", "risk management", "audit", "compliance"]
            },
            "rh": {
                "tools": ["workday", "successfactors", "adp", "bamboohr"],
                "concepts": ["talent acquisition", "performance management", "employee engagement"],
                "skills": ["recruitment", "onboarding", "compensation", "benefits"],
                "legal": ["employment law", "diversity", "inclusion", "compliance"]
            }
        }
        
        # Formatage problématique pour les ATS
        self.ats_formatting_issues = {
            "complex_tables": r'\|.*\|.*\|',
            "special_characters": r'[★☆♦♠♥♣●◆■□▲▼]',
            "multiple_columns": r'\t.*\t.*\t',
            "headers_footers": r'(page \d+|\d+/\d+)',
            "graphics": r'(image|figure|chart|graph)'
        }

    def analyze_ats_compatibility(self, 
                                letter_content: str,
                                job_description: str,
                                target_sector: Optional[str] = None,
                                user_tier: UserTier = UserTier.FREE) -> ATSAnalysis:
        """
        Analyse la compatibilité ATS d'une lettre de motivation.
        
        Args:
            letter_content: Contenu de la lettre
            job_description: Description du poste
            target_sector: Secteur cible (optionnel)
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            ATSAnalysis: Analyse complète ATS
        """
        if user_tier == UserTier.FREE:
            logger.info("ATS Analysis is a premium feature. Returning default for Free user.")
            return self._get_fallback_analysis(letter_content, job_description, is_premium_feature=True)

        try:
            logger.info("Starting ATS compatibility analysis")
            
            # Validation et nettoyage
            clean_letter = self.input_validator.sanitize_text_input(letter_content)
            clean_job_desc = self.input_validator.sanitize_text_input(job_description)
            
            # Extraction des mots-clés du poste
            job_keywords = self._extract_job_keywords(clean_job_desc, target_sector)
            
            # Analyse des correspondances
            matched_keywords, missing_keywords = self._analyze_keyword_matches(clean_letter, job_keywords)
            
            # Calcul de la densité des mots-clés
            keyword_density = self._calculate_keyword_density(clean_letter, matched_keywords)
            
            # Score de compatibilité ATS
            ats_score = self._calculate_ats_score(matched_keywords, job_keywords, clean_letter)
            
            # Analyse du formatage
            formatting_score = self._analyze_formatting(clean_letter)
            
            # Analyse des verbes d'action
            action_verbs_score = self._analyze_action_verbs(clean_letter)
            
            # Comptage des accomplissements quantifiés
            quantifiable_achievements = self._count_quantifiable_achievements(clean_letter)
            
            # Génération des recommandations
            recommendations = self._generate_ats_recommendations(
                matched_keywords, missing_keywords, formatting_score, action_verbs_score
            )
            
            # Suggestions d'optimisation
            optimized_suggestions = self._generate_optimization_suggestions(
                clean_letter, missing_keywords
            )
            
            # Termes spécifiques au secteur
            industry_terms = self._identify_industry_terms(clean_letter, target_sector)
            
            analysis = ATSAnalysis(
                letter_content=clean_letter,
                job_keywords=job_keywords,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords,
                keyword_density=keyword_density,
                ats_compatibility_score=ats_score,
                formatting_score=formatting_score,
                recommendations=recommendations,
                optimized_suggestions=optimized_suggestions,
                industry_specific_terms=industry_terms,
                action_verbs_score=action_verbs_score,
                quantifiable_achievements_count=quantifiable_achievements
            )
            
            logger.info(f"ATS analysis completed - Score: {ats_score}/100")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in ATS analysis: {e}")
            return self._get_fallback_analysis(letter_content, job_description)

    def _extract_job_keywords(self, job_description: str, target_sector: Optional[str]) -> List[str]:
        """Extrait les mots-clés importants de la description de poste."""
        keywords = set()
        
        # Nettoyage du texte
        job_lower = job_description.lower()
        
        # Extraction de mots-clés techniques et compétences
        # Patterns pour identifier les compétences
        skill_patterns = [
            r'compétence[s]?\s*:?\s*([^\.]+)',
            r'requis[e]?\s*:?\s*([^\.]+)',
            r'maîtrise\s+(?:de\s+)?([^\.]+)',
            r'expérience\s+(?:en\s+|avec\s+)?([^\.]+)',
            r'connaissance\s+(?:de\s+|en\s+)?([^\.]+)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            for match in matches:
                # Extraction des termes individuels
                terms = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#]*\b', match)
                keywords.update([term for term in terms if len(term) > 2])
        
        # Ajout de mots-clés sectoriels
        if target_sector and target_sector in self.sector_keywords:
            sector_data = self.sector_keywords[target_sector]
            for category_keywords in sector_data.values():
                for keyword in category_keywords:
                    if keyword.lower() in job_lower:
                        keywords.add(keyword)
        
        # Extraction de certifications et outils mentionnés
        cert_patterns = [
            r'\b[A-Z]{2,5}\b',  # Acronymes (AWS, PMP, etc.)
            r'\b\w+(?:\s+certified?|\s+certification)\b',
            r'\b(?:microsoft|google|amazon|adobe|oracle|sap)\s+\w+\b'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            keywords.update([match.strip() for match in matches])
        
        # Filtrage et priorisation
        filtered_keywords = self._filter_and_prioritize_keywords(list(keywords), job_description)
        
        return filtered_keywords[:25]  # Limiter à 25 mots-clés principaux

    def _filter_and_prioritize_keywords(self, keywords: List[str], job_description: str) -> List[str]:
        """Filtre et priorise les mots-clés par importance."""
        # Mots à exclure
        stop_words = {
            "and", "or", "the", "in", "on", "at", "to", "for", "of", "with", "by",
            "vous", "nous", "les", "des", "une", "dans", "pour", "sur", "avec"
        }
        
        # Filtrage
        valid_keywords = []
        for keyword in keywords:
            if (len(keyword) > 2 and 
                keyword.lower() not in stop_words and
                not keyword.isdigit() and
                re.match(r'^[a-zA-Z0-9+#\s-]+$', keyword)):
                valid_keywords.append(keyword)
        
        # Priorisation par fréquence dans le texte
        keyword_counts = Counter()
        job_lower = job_description.lower()
        
        for keyword in valid_keywords:
            count = job_lower.count(keyword.lower())
            keyword_counts[keyword] = count
        
        # Retourner les mots-clés triés par importance
        return [kw for kw, count in keyword_counts.most_common()]

    def _analyze_keyword_matches(self, letter_content: str, job_keywords: List[str]) -> Tuple[List[str], List[str]]:
        """Analyse les correspondances de mots-clés."""
        letter_lower = letter_content.lower()
        matched = []
        missing = []
        
        for keyword in job_keywords:
            # Recherche flexible (exact match et variations)
            keyword_lower = keyword.lower()
            if (keyword_lower in letter_lower or 
                any(variant in letter_lower for variant in self._generate_keyword_variants(keyword))):
                matched.append(keyword)
            else:
                missing.append(keyword)
        
        return matched, missing

    def _generate_keyword_variants(self, keyword: str) -> List[str]:
        """Génère des variantes d'un mot-clé."""
        variants = [keyword.lower()]
        
        # Variantes courantes
        if keyword.endswith('ing'):
            variants.append(keyword[:-3])  # programming -> program
        if keyword.endswith('ed'):
            variants.append(keyword[:-2])  # managed -> manage
        if keyword.endswith('ment'):
            variants.append(keyword[:-4])  # management -> manage
        
        # Acronymes
        if len(keyword) > 6:
            acronym = ''.join([c for c in keyword if c.isupper()])
            if len(acronym) > 1:
                variants.append(acronym.lower())
        
        return variants

    def _calculate_keyword_density(self, letter_content: str, matched_keywords: List[str]) -> Dict[str, float]:
        """Calcule la densité des mots-clés dans la lettre."""
        total_words = len(letter_content.split())
        density = {}
        
        for keyword in matched_keywords:
            count = letter_content.lower().count(keyword.lower())
            density[keyword] = round((count / total_words) * 100, 2) if total_words > 0 else 0
        
        return density

    def _calculate_ats_score(self, matched_keywords: List[str], 
                           job_keywords: List[str], letter_content: str) -> float:
        """Calcule le score global de compatibilité ATS."""
        if not job_keywords:
            return 50.0
        
        # Score de base sur les mots-clés
        keyword_match_rate = len(matched_keywords) / len(job_keywords)
        keyword_score = keyword_match_rate * 60  # 60% du score max
        
        # Bonus pour la qualité du contenu
        word_count = len(letter_content.split())
        length_bonus = 5 if 200 <= word_count <= 400 else 0  # Longueur idéale
        
        # Bonus pour les verbes d'action
        action_verb_count = sum(1 for verb in self.strong_action_verbs 
                               if verb in letter_content.lower())
        action_bonus = min(10, action_verb_count * 2)
        
        # Bonus pour les résultats quantifiés
        quantified_count = len(re.findall(r'\d+%|\d+€|\d+\s*(?:ans?|années?)', letter_content))
        quantified_bonus = min(10, quantified_count * 3)
        
        # Malus pour les problèmes de formatage
        formatting_issues = sum(1 for pattern in self.ats_formatting_issues.values()
                              if re.search(pattern, letter_content, re.IGNORECASE))
        formatting_malus = formatting_issues * 5
        
        total_score = keyword_score + length_bonus + action_bonus + quantified_bonus - formatting_malus
        return round(max(0, min(100, total_score)), 1)

    def _analyze_formatting(self, letter_content: str) -> float:
        """Analyse la qualité du formatage pour les ATS."""
        score = 100.0
        
        # Vérifications de formatage
        checks = [
            ("Caractères spéciaux problématiques", self.ats_formatting_issues["special_characters"], -10),
            ("Tableaux complexes", self.ats_formatting_issues["complex_tables"], -15),
            ("Colonnes multiples", self.ats_formatting_issues["multiple_columns"], -10),
            ("En-têtes/pieds de page", self.ats_formatting_issues["headers_footers"], -5)
        ]
        
        issues_found = []
        for check_name, pattern, penalty in checks:
            if re.search(pattern, letter_content, re.IGNORECASE):
                score += penalty
                issues_found.append(check_name)
        
        # Bonus pour un formatage simple et propre
        if not issues_found:
            score += 10
        
        # Vérification de la structure (paragraphes)
        paragraph_count = letter_content.count('\n\n') + 1
        if 3 <= paragraph_count <= 5:
            score += 5
        
        return round(max(0, min(100, score)), 1)

    def _analyze_action_verbs(self, letter_content: str) -> float:
        """Analyse l'utilisation de verbes d'action forts."""
        content_lower = letter_content.lower()
        
        # Comptage des verbes d'action présents
        action_verbs_found = [verb for verb in self.strong_action_verbs 
                             if verb in content_lower]
        
        # Score basé sur la diversité et la quantité
        unique_verbs = len(set(action_verbs_found))
        total_usage = len(action_verbs_found)
        
        # Score = diversité (40%) + usage total (60%)
        diversity_score = min(40, unique_verbs * 5)
        usage_score = min(60, total_usage * 6)
        
        return round(diversity_score + usage_score, 1)

    def _count_quantifiable_achievements(self, letter_content: str) -> int:
        """Compte les accomplissements quantifiés."""
        # Patterns pour les résultats quantifiés
        patterns = [
            r'\d+%',  # Pourcentages
            r'\d+€',  # Montants en euros
            r'\d+\s*(?:millions?|milliers?|k€)',  # Montants avec unités
            r'\d+\s*(?:ans?|années?)',  # Années d'expérience
            r'\d+\s*(?:projets?|clients?|personnes?)',  # Quantités
            r'(?:augmenté|réduit|amélioré|économisé).*?\d+',  # Améliorations chiffrées
        ]
        
        total_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, letter_content, re.IGNORECASE)
            total_count += len(matches)
        
        return total_count

    def _generate_ats_recommendations(self, matched_keywords: List[str], 
                                    missing_keywords: List[str],
                                    formatting_score: float,
                                    action_verbs_score: float) -> List[str]:
        """Génère des recommandations d'optimisation ATS."""
        recommendations = []
        
        # Recommandations sur les mots-clés
        if len(missing_keywords) > len(matched_keywords):
            recommendations.append(
                f"Intégrez davantage de mots-clés du poste : {', '.join(missing_keywords[:5])}"
            )
        
        keyword_match_rate = len(matched_keywords) / (len(matched_keywords) + len(missing_keywords)) if (matched_keywords or missing_keywords) else 0
        if keyword_match_rate < 0.4:
            recommendations.append(
                "Taux de correspondance des mots-clés faible (<40%). Personnalisez davantage votre lettre."
            )
        
        # Recommandations sur le formatage
        if formatting_score < 80:
            recommendations.append(
                "Simplifiez le formatage : évitez les caractères spéciaux et tableaux complexes."
            )
        
        # Recommandations sur les verbes d'action
        if action_verbs_score < 50:
            recommendations.append(
                "Utilisez plus de verbes d'action forts pour dynamiser votre lettre."
            )
        
        # Recommandations générales
        recommendations.extend([
            "Utilisez des mots-clés naturellement dans le contexte.",
            "Quantifiez vos accomplissements avec des chiffres précis.",
            "Maintenez une structure claire avec des paragraphes distincts."
        ])
        
        return recommendations[:5]  # Limiter à 5 recommandations

    def _generate_optimization_suggestions(self, letter_content: str, 
                                         missing_keywords: List[str]) -> Dict[str, str]:
        """Génère des suggestions d'optimisation phrase par phrase."""
        suggestions = {}
        
        # Analyse par phrases
        sentences = [s.strip() for s in letter_content.split('.') if s.strip()]
        
        for i, sentence in enumerate(sentences[:3]):  # Analyser les 3 premières phrases
            if len(sentence.split()) > 30:  # Phrase trop longue
                suggestions[sentence[:50] + "..."] = "Phrase trop longue - divisez en phrases plus courtes"
            
            # Vérifier la présence de verbes faibles
            weak_verbs = ["faire", "avoir", "être"]
            if any(verb in sentence.lower() for verb in weak_verbs):
                suggestions[sentence[:50] + "..."] = "Remplacez les verbes faibles par des verbes d'action"
        
        # Suggestions pour intégrer les mots-clés manquants
        if missing_keywords:
            top_missing = missing_keywords[:3]
            suggestions["Mots-clés manquants"] = f"Intégrez naturellement : {', '.join(top_missing)}"
        
        return suggestions

    def _identify_industry_terms(self, letter_content: str, target_sector: Optional[str]) -> List[str]:
        """Identifie les termes spécifiques au secteur utilisés."""
        if not target_sector or target_sector not in self.sector_keywords:
            return []
        
        content_lower = letter_content.lower()
        found_terms = []
        
        sector_data = self.sector_keywords[target_sector]
        for category_terms in sector_data.values():
            for term in category_terms:
                if term.lower() in content_lower:
                    found_terms.append(term)
        
        return list(set(found_terms))  # Supprimer les doublons

    def generate_ats_optimized_version(self, letter_content: str, 
                                     missing_keywords: List[str],
                                     max_keywords_to_add: int = 5,
                                     user_tier: UserTier = UserTier.FREE) -> str:
        """Génère une version optimisée ATS de la lettre."""
        try:
            # Sélectionner les mots-clés les plus importants à ajouter
            keywords_to_add = missing_keywords[:max_keywords_to_add]
            
            prompt = f"""
            Optimisez cette lettre de motivation pour les systèmes ATS en intégrant naturellement 
            ces mots-clés manquants : {', '.join(keywords_to_add)}
            
            LETTRE ORIGINALE :
            {letter_content}
            
            CONSIGNES :
            1. Intégrez les mots-clés de manière naturelle et contextuelle
            2. Maintenez le ton professionnel et la cohérence
            3. Ne dépassez pas 400 mots
            4. Utilisez des verbes d'action forts
            5. Gardez une structure claire avec 3-4 paragraphes
            
            Retournez UNIQUEMENT la lettre optimisée.
            """
            
            optimized_letter = self.ai_client.generate_content(prompt=prompt, temperature=0.3, max_tokens=600, user_tier=user_tier)
            return optimized_letter.strip()
            
        except Exception as e:
            logger.warning(f"ATS optimization failed: {e}")
            return letter_content

    def _get_fallback_analysis(self, letter_content: str, job_description: str, is_premium_feature: bool = False) -> ATSAnalysis:
        """Analyse de secours en cas d'erreur."""
        if is_premium_feature:
            return ATSAnalysis(
                letter_content=letter_content,
                job_keywords=["Fonctionnalité Premium"],
                matched_keywords=["N/A"],
                missing_keywords=["N/A"],
                keyword_density={"N/A": 0.0},
                ats_compatibility_score=0.0,
                formatting_score=0.0,
                recommendations=[
                    "Cette fonctionnalité est réservée aux utilisateurs Premium.",
                    "Passez Premium pour débloquer l'analyse ATS."
                ],
                optimized_suggestions={"note": "Fonctionnalité Premium"},
                industry_specific_terms=["N/A"],
                action_verbs_score=0.0,
                quantifiable_achievements_count=0
            )
        return ATSAnalysis(
            letter_content=letter_content,
            job_keywords=["Analyse requise"],
            matched_keywords=["Correspondances à analyser"],
            missing_keywords=["Mots-clés manquants à identifier"],
            keyword_density={"analyse": 0.0},
            ats_compatibility_score=50.0,
            formatting_score=75.0,
            recommendations=[
                "Service d'analyse temporairement indisponible",
                "Vérifiez manuellement la correspondance avec les mots-clés du poste",
                "Utilisez un formatage simple et professionnel"
            ],
            optimized_suggestions={"note": "Optimisation manuelle recommandée"},
            industry_specific_terms=["Termes sectoriels à identifier"],
            action_verbs_score=50.0,
            quantifiable_achievements_count=0
        )