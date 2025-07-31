"""Service RAG avancé pour personnalisation lettres de motivation."""
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


@dataclass
class UserContext:
    """Contexte utilisateur enrichi pour RAG."""
    user_id: str
    sector_source: str      # Secteur actuel
    sector_target: str      # Secteur cible
    role_target: str        # Poste cible
    experience_years: int   # Années d'expérience
    skills: List[str]       # Compétences identifiées
    previous_letters: List[Dict[str, Any]]  # Historique lettres
    preferences: Dict[str, Any]             # Préférences utilisateur
    reconversion_type: str  # "lateral", "vertical", "pivot"
    urgency_level: str      # "low", "medium", "high"
    last_updated: datetime


@dataclass
class RAGDocument:
    """Document pour base de connaissances RAG."""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    relevance_score: float = 0.0


@dataclass
class PersonalizationContext:
    """Contexte de personnalisation pour génération."""
    user_context: UserContext
    relevant_examples: List[RAGDocument]
    sector_insights: Dict[str, Any]
    personalization_strategy: str
    confidence_score: float


class RAGPersonalizationService:
    """Service RAG pour personnalisation avancée des lettres."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Base de connaissances en mémoire (à migrer vers vraie DB)
        self.knowledge_base: Dict[str, RAGDocument] = {}
        self.user_contexts: Dict[str, UserContext] = {}
        
        # Templates de lettres par secteur/reconversion
        self.letter_templates = self._init_letter_templates()
        
        # Insights sectoriels 
        self.sector_insights = self._init_sector_insights()
        
        # Patterns de reconversion
        self.reconversion_patterns = self._init_reconversion_patterns()
    
    def _init_letter_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialise templates de lettres par secteur."""
        return {
            "tech": {
                "opening": [
                    "Passionné(e) par l'innovation technologique et les défis techniques",
                    "Fort(e) d'une expérience en {sector_source}, je souhaite mettre mes compétences au service de l'écosystème tech",
                    "Ma transition vers le secteur technologique s'appuie sur {transferable_skills}"
                ],
                "middle": [
                    "Mon expertise en {key_skill} me permettra de contribuer efficacement à vos projets",
                    "Mes réalisations en {sector_source} démontrent ma capacité d'adaptation et d'apprentissage rapide"
                ],
                "closing": [
                    "Je serais ravi(e) d'échanger sur les synergies entre mon profil et vos besoins techniques",
                    "Disponible pour un entretien technique pour démontrer mes compétences"
                ]
            },
            
            "marketing": {
                "opening": [
                    "Créatif(ve) et orienté(e) résultats, je souhaite apporter ma vision stratégique au marketing",
                    "Ma reconversion vers le marketing digital s'appuie sur {years} années d'expérience client"
                ],
                "middle": [
                    "Mes succès en {sector_source} m'ont permis de développer une compréhension fine des besoins clients",
                    "Mon approche data-driven et ma créativité seront des atouts pour vos campagnes"
                ],
                "closing": [
                    "Enthousiaste à l'idée de contribuer à votre stratégie marketing",
                    "Prêt(e) à présenter des idées concrètes pour vos prochaines campagnes"
                ]
            },
            
            "finance": {
                "opening": [
                    "Rigoureux(se) et analytique, je souhaite mettre mon expertise au service de la finance",
                    "Ma transition vers la finance s'appuie sur {years} années d'analyse et de gestion"
                ],
                "middle": [
                    "Mon expérience en {sector_source} m'a formé(e) à l'analyse de données complexes",
                    "Ma rigueur et mon attention aux détails sont des atouts essentiels en finance"
                ],
                "closing": [
                    "Disponible pour échanger sur mes compétences analytiques",
                    "Prêt(e) à contribuer à l'optimisation de vos processus financiers"
                ]
            }
        }
    
    def _init_sector_insights(self) -> Dict[str, Dict[str, Any]]:
        """Initialise insights par secteur."""
        return {
            "tech": {
                "key_values": ["innovation", "agilité", "collaboration", "apprentissage continu"],
                "must_have_skills": ["problem-solving", "adaptabilité", "veille technologique"],
                "communication_style": "direct, technique, orienté solution",
                "red_flags": ["manque de curiosité technique", "résistance au changement"],
                "trending_keywords": ["IA", "cloud", "DevOps", "cybersécurité", "data"]
            },
            
            "marketing": {
                "key_values": ["créativité", "ROI", "customer-centric", "data-driven"],
                "must_have_skills": ["storytelling", "analyse de données", "gestion de projet"],
                "communication_style": "créatif, persuasif, orienté résultats",
                "red_flags": ["manque de mesure ROI", "créativité sans stratégie"],
                "trending_keywords": ["growth hacking", "personalization", "omnichannel", "automation"]
            },
            
            "finance": {
                "key_values": ["rigueur", "conformité", "optimisation", "maîtrise des risques"],
                "must_have_skills": ["analyse financière", "gestion des risques", "reporting"],
                "communication_style": "précis, factuel, orienté chiffres",
                "red_flags": ["approximations", "manque de rigueur", "non-conformité"],
                "trending_keywords": ["fintech", "blockchain", "ESG", "risk management", "automation"]
            }
        }
    
    def _init_reconversion_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialise patterns de reconversion réussies."""
        return {
            "lateral": {  # Même niveau hiérarchique, secteur différent
                "description": "Reconversion horizontale avec transfert compétences",
                "success_factors": ["compétences transférables", "réseau professionnel", "formation complémentaire"],
                "timeline": "3-6 mois",
                "key_message": "Apporter expertise sectorielle avec vision externe"
            },
            
            "vertical": {  # Évolution hiérarchique avec reconversion
                "description": "Montée en responsabilités avec changement secteur",
                "success_factors": ["leadership prouvé", "vision stratégique", "expertise métier"],
                "timeline": "6-12 mois", 
                "key_message": "Combiner expertise management et vision transverse"
            },
            
            "pivot": {  # Changement radical de domaine
                "description": "Reconversion complète vers nouveau domaine",
                "success_factors": ["formation intensive", "motivation forte", "adaptabilité"],
                "timeline": "12-18 mois",
                "key_message": "Apporter fraîcheur et perspective nouvelle"
            }
        }
    
    def build_user_context(
        self,
        user_id: str,
        cv_content: str,
        target_role: str,
        target_sector: str,
        additional_info: Dict[str, Any] = None
    ) -> UserContext:
        """
        Construit contexte utilisateur enrichi pour RAG.
        
        Args:
            user_id: ID utilisateur
            cv_content: Contenu CV
            target_role: Poste cible
            target_sector: Secteur cible
            additional_info: Infos supplémentaires
        Returns:
            UserContext enrichi
        """
        
        # Analyser CV pour extraire insights
        cv_analysis = self._analyze_cv_content(cv_content)
        
        # Déterminer type de reconversion
        reconversion_type = self._determine_reconversion_type(
            cv_analysis["current_sector"], 
            target_sector,
            cv_analysis["experience_years"]
        )
        
        # Construire contexte
        context = UserContext(
            user_id=user_id,
            sector_source=cv_analysis["current_sector"],
            sector_target=target_sector,
            role_target=target_role,
            experience_years=cv_analysis["experience_years"],
            skills=cv_analysis["skills"],
            previous_letters=self._get_user_letter_history(user_id),
            preferences=additional_info or {},
            reconversion_type=reconversion_type,
            urgency_level=additional_info.get("urgency", "medium"),
            last_updated=datetime.now()
        )
        
        # Sauvegarder contexte
        self.user_contexts[user_id] = context
        
        return context
    
    def _analyze_cv_content(self, cv_content: str) -> Dict[str, Any]:
        """Analyse contenu CV pour extraire insights."""
        
        # Analyse simplifiée (à améliorer avec NLP)
        skills = []
        current_sector = "général"
        experience_years = 0
        
        # Extraction basique de compétences
        cv_lower = cv_content.lower()
        
        # Compétences techniques
        tech_skills = ["python", "javascript", "sql", "excel", "powerbi", "tableau", "git"]
        skills.extend([skill for skill in tech_skills if skill in cv_lower])
        
        # Compétences marketing
        marketing_skills = ["seo", "google ads", "analytics", "content marketing", "social media"]
        skills.extend([skill for skill in marketing_skills if skill in cv_lower])
        
        # Détection secteur via mots-clés
        if any(word in cv_lower for word in ["développeur", "programmeur", "data", "technique"]):
            current_sector = "tech"
        elif any(word in cv_lower for word in ["marketing", "communication", "digital", "campagne"]):
            current_sector = "marketing"
        elif any(word in cv_lower for word in ["finance", "comptable", "audit", "budget"]):
            current_sector = "finance"
        
        # Estimation années d'expérience (très approximative)
        import re
        years_mentions = re.findall(r'(\d+)\s*(?:ans?|années?)', cv_lower)
        if years_mentions:
            experience_years = max([int(year) for year in years_mentions])
        
        return {
            "skills": skills,
            "current_sector": current_sector,
            "experience_years": experience_years,
            "estimated_seniority": "junior" if experience_years < 3 else "senior" if experience_years > 7 else "middle"
        }
    
    def _determine_reconversion_type(self, source_sector: str, target_sector: str, experience: int) -> str:
        """Détermine type de reconversion."""
        
        if source_sector == target_sector:
            return "lateral"  # Même secteur, évolution de poste
        
        # Secteurs proches
        related_sectors = {
            "tech": ["marketing", "finance"],
            "marketing": ["tech", "communication"],
            "finance": ["tech", "consulting"]
        }
        
        if target_sector in related_sectors.get(source_sector, []):
            return "vertical" if experience > 5 else "lateral"
        
        return "pivot"  # Changement radical
    
    def _get_user_letter_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Récupère historique lettres utilisateur."""
        # TODO: Implémenter récupération depuis BDD
        return []
    
    def retrieve_relevant_context(
        self, 
        user_context: UserContext, 
        job_offer: str,
        max_examples: int = 5
    ) -> PersonalizationContext:
        """
        Récupère contexte de personnalisation via RAG.
        
        Args:
            user_context: Contexte utilisateur
            job_offer: Offre d'emploi
            max_examples: Nombre max d'exemples
        Returns:
            PersonalizationContext pour génération
        """
        
        # 1. Rechercher exemples similaires
        relevant_examples = self._find_similar_examples(
            user_context, job_offer, max_examples
        )
        
        # 2. Récupérer insights sectoriels
        sector_insights = self.sector_insights.get(
            user_context.sector_target, 
            self.sector_insights["tech"]  # Fallback
        )
        
        # 3. Déterminer stratégie de personnalisation
        personalization_strategy = self._determine_personalization_strategy(user_context)
        
        # 4. Calculer score de confiance
        confidence_score = self._calculate_confidence_score(
            user_context, relevant_examples, sector_insights
        )
        
        context = PersonalizationContext(
            user_context=user_context,
            relevant_examples=relevant_examples,
            sector_insights=sector_insights,
            personalization_strategy=personalization_strategy,
            confidence_score=confidence_score
        )
        
        return context
    
    def _find_similar_examples(
        self, 
        user_context: UserContext, 
        job_offer: str, 
        max_examples: int
    ) -> List[RAGDocument]:
        """Trouve exemples similaires dans base de connaissances."""
        
        # Pour démo, retourner exemples statiques
        # TODO: Implémenter recherche par embeddings
        
        examples = []
        
        # Exemple pour tech
        if user_context.sector_target == "tech":
            examples.append(RAGDocument(
                doc_id="tech_example_1",
                content="Exemple lettre reconversion vers tech avec focus sur problem-solving",
                metadata={
                    "sector_source": user_context.sector_source,
                    "sector_target": "tech",
                    "success_rate": 0.85,
                    "reconversion_type": user_context.reconversion_type
                },
                relevance_score=0.9
            ))
        
        return examples[:max_examples]
    
    def _determine_personalization_strategy(self, user_context: UserContext) -> str:
        """Détermine stratégie de personnalisation optimale."""
        
        strategies = {
            "pivot": "emphasize_transferable_skills",
            "lateral": "highlight_sector_expertise", 
            "vertical": "showcase_leadership_growth"
        }
        
        return strategies.get(user_context.reconversion_type, "balanced_approach")
    
    def _calculate_confidence_score(
        self,
        user_context: UserContext,
        examples: List[RAGDocument],
        sector_insights: Dict[str, Any]
    ) -> float:
        """Calcule score de confiance pour personnalisation."""
        
        score = 0.5  # Base score
        
        # Plus d'exemples similaires = plus de confiance
        if len(examples) > 3:
            score += 0.2
        
        # Expérience utilisateur
        if user_context.experience_years > 5:
            score += 0.1
        
        # Reconversion type
        if user_context.reconversion_type == "lateral":
            score += 0.1  # Plus facile
        elif user_context.reconversion_type == "pivot":
            score -= 0.1  # Plus difficile
        
        # Compétences identifiées
        if len(user_context.skills) > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def generate_personalized_prompt(self, personalization_context: PersonalizationContext) -> str:
        """
        Génère prompt personnalisé basé sur contexte RAG.
        
        Args:
            personalization_context: Contexte de personnalisation
        Returns:
            Prompt enrichi pour génération IA
        """
        
        user_ctx = personalization_context.user_context
        insights = personalization_context.sector_insights
        strategy = personalization_context.personalization_strategy
        
        # Template base selon secteur cible
        templates = self.letter_templates.get(user_ctx.sector_target, self.letter_templates["tech"])
        
        # Construire prompt enrichi
        enriched_prompt = f"""
CONTEXTE DE RECONVERSION PROFESSIONNELLE :
- Secteur actuel : {user_ctx.sector_source}
- Secteur cible : {user_ctx.sector_target}  
- Type reconversion : {user_ctx.reconversion_type}
- Années expérience : {user_ctx.experience_years}
- Compétences clés : {', '.join(user_ctx.skills[:5])}

INSIGHTS SECTEUR CIBLE ({user_ctx.sector_target.upper()}) :
- Valeurs clés : {', '.join(insights['key_values'])}
- Compétences recherchées : {', '.join(insights['must_have_skills'])}
- Style communication : {insights['communication_style']}
- Mots-clés tendance : {', '.join(insights['trending_keywords'])}

STRATÉGIE DE PERSONNALISATION : {strategy}

TEMPLATES SECTORIELS RECOMMANDÉS :
{json.dumps(templates, indent=2, ensure_ascii=False)}

PATTERN DE RECONVERSION ({user_ctx.reconversion_type.upper()}) :
{json.dumps(self.reconversion_patterns[user_ctx.reconversion_type], indent=2, ensure_ascii=False)}

INSTRUCTIONS GÉNÉRATION :
1. Utiliser le template sectoriel approprié comme structure
2. Intégrer naturellement les mots-clés tendance du secteur
3. Adapter le ton selon le style de communication sectoriel
4. Mettre en avant les compétences transférables pertinentes
5. Suivre la stratégie de personnalisation définie
6. Éviter les red flags identifiés pour le secteur

Générez une lettre de motivation personnalisée et percutante.
"""
        
        return enriched_prompt
    
    def add_to_knowledge_base(self, document: RAGDocument) -> None:
        """Ajoute document à la base de connaissances."""
        self.knowledge_base[document.doc_id] = document
        self.logger.info(f"Added document to knowledge base: {document.doc_id}")
    
    def get_personalization_metrics(self) -> Dict[str, Any]:
        """Retourne métriques de personnalisation."""
        return {
            "total_users": len(self.user_contexts),
            "knowledge_base_size": len(self.knowledge_base),
            "reconversion_types": {
                reconversion_type: len([
                    ctx for ctx in self.user_contexts.values() 
                    if ctx.reconversion_type == reconversion_type
                ])
                for reconversion_type in ["lateral", "vertical", "pivot"]
            },
            "top_target_sectors": {
                sector: len([
                    ctx for ctx in self.user_contexts.values()
                    if ctx.sector_target == sector
                ])
                for sector in ["tech", "marketing", "finance"]
            }
        }