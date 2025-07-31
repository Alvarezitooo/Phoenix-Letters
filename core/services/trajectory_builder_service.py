"""Service Trajectory Builder - Plans de reconversion personnalisés."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

from core.entities.letter import ReconversionPlan, TrajectoryStep, UserTier
from shared.interfaces.ai_interface import AIServiceInterface
from infrastructure.security.input_validator import InputValidator

logger = logging.getLogger(__name__)

class TrajectoryBuilderService:
    """Service de création de plans de reconversion personnalisés."""
    
    def __init__(self, ai_client: AIServiceInterface, input_validator: InputValidator):
        self.ai_client = ai_client
        self.input_validator = input_validator
        
        # Base de données des compétences par secteur
        self.sector_skills = {
            "tech": {
                "core": ["programmation", "algorithmique", "base de données", "architecture logicielle"],
                "trending": ["ia/ml", "cloud computing", "devops", "cybersécurité", "blockchain"],
                "soft": ["résolution de problèmes", "pensée analytique", "veille technologique"]
            },
            "marketing": {
                "core": ["stratégie marketing", "communication", "analyse de marché", "gestion de projet"],
                "trending": ["marketing digital", "data analytics", "automation", "content marketing"],
                "soft": ["créativité", "persuasion", "adaptabilité", "orientation client"]
            },
            "rh": {
                "core": ["recrutement", "gestion des talents", "droit du travail", "formation"],
                "trending": ["hr analytics", "transformation digitale", "wellbeing", "diversité"],
                "soft": ["empathie", "communication", "négociation", "leadership"]
            },
            "finance": {
                "core": ["comptabilité", "analyse financière", "gestion des risques", "conformité"],
                "trending": ["fintech", "robo-advisory", "crypto", "esg investing"],
                "soft": ["rigueur", "analyse critique", "éthique", "prise de décision"]
            },
            "sante": {
                "core": ["diagnostic", "soins patients", "protocoles médicaux", "éthique médicale"],
                "trending": ["télémédecine", "médecine personnalisée", "data health", "robotique médicale"],
                "soft": ["empathie", "résistance au stress", "travail d'équipe", "précision"]
            }
        }
        
        # Difficultés de transition par secteur
        self.transition_difficulty = {
            ("finance", "tech"): "challenging",
            ("marketing", "tech"): "moderate", 
            ("rh", "tech"): "moderate",
            ("sante", "tech"): "challenging",
            ("tech", "marketing"): "easy",
            ("tech", "finance"): "moderate",
            ("marketing", "rh"): "easy",
            ("finance", "rh"): "easy"
        }

    def create_reconversion_plan(self, 
                                user_id: str,
                                current_role: str,
                                target_role: str,
                                current_skills: List[str],
                                cv_content: Optional[str] = None,
                                target_job_description: Optional[str] = None,
                                timeline_months: Optional[int] = None,
                                user_tier: UserTier = UserTier.FREE) -> ReconversionPlan:
        """
        Crée un plan de reconversion personnalisé.
        
        Args:
            user_id: Identifiant utilisateur
            current_role: Poste actuel
            target_role: Poste visé
            current_skills: Compétences actuelles
            cv_content: Contenu du CV pour analyse approfondie
            target_job_description: Description du poste cible
            timeline_months: Durée souhaitée (par défaut calculée automatiquement)
            user_tier: Niveau d'abonnement de l'utilisateur
            
        Returns:
            ReconversionPlan: Plan de reconversion complet
        """
        if user_tier == UserTier.FREE:
            logger.info("Trajectory Builder is a premium feature. Returning default for Free user.")
            return self._get_fallback_plan(user_id, current_role, target_role, is_premium_feature=True)

        try:
            logger.info(f"Creating reconversion plan: {current_role} -> {target_role}")
            
            # Validation des entrées
            current_role = self.input_validator.sanitize_text_input(current_role)
            target_role = self.input_validator.sanitize_text_input(target_role)
            
            # Analyse des secteurs
            current_sector = self._identify_sector(current_role)
            target_sector = self._identify_sector(target_role)
            
            # Analyse des compétences requises
            target_skills = self._analyze_target_skills(target_role, target_job_description, user_tier)
            
            # Identification des lacunes
            skill_gaps = self._identify_skill_gaps(current_skills, target_skills)
            
            # Évaluation de la difficulté
            difficulty_level = self._assess_difficulty(current_sector, target_sector, skill_gaps)
            
            # Calcul de la probabilité de succès
            success_probability = self._calculate_success_probability(
                current_skills, target_skills, difficulty_level
            )
            
            # Génération des étapes du parcours
            trajectory_steps = self._generate_trajectory_steps(
                current_sector, target_sector, skill_gaps, timeline_months
            )
            
            # Estimation de la durée
            estimated_duration = timeline_months or self._estimate_duration(difficulty_level, len(skill_gaps))
            
            # Ressources recommandées
            recommended_resources = self._get_recommended_resources(target_sector, skill_gaps)
            
            # Insights sectoriels
            industry_insights = self._get_industry_insights(target_sector)
            
            plan = ReconversionPlan(
                user_id=user_id,
                current_role=current_role,
                target_role=target_role,
                current_skills=current_skills,
                target_skills=target_skills,
                skill_gaps=skill_gaps,
                trajectory_steps=trajectory_steps,
                estimated_duration_months=estimated_duration,
                difficulty_level=difficulty_level,
                success_probability=success_probability,
                recommended_resources=recommended_resources,
                industry_insights=industry_insights,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            logger.info(f"Reconversion plan created - Duration: {estimated_duration}m, Success: {success_probability:.1%}")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating reconversion plan: {e}")
            return self._get_fallback_plan(user_id, current_role, target_role)

    def _identify_sector(self, role: str) -> str:
        """Identifie le secteur à partir du titre de poste."""
        role_lower = role.lower()
        
        # Mots-clés par secteur
        sector_keywords = {
            "tech": ["développeur", "ingénieur", "data", "it", "informatique", "web", "mobile", "devops"],
            "marketing": ["marketing", "communication", "digital", "brand", "publicité", "content"],
            "rh": ["rh", "ressources humaines", "recrutement", "talent", "formation", "paie"],
            "finance": ["finance", "comptable", "audit", "contrôle", "gestion", "banque", "assurance"],
            "sante": ["médecin", "infirmier", "pharmacien", "santé", "médical", "thérapie", "soin"],
            "commercial": ["commercial", "vente", "business", "account", "sales", "client"],
            "education": ["professeur", "enseignant", "formation", "éducation", "pédagogie"],
            "juridique": ["avocat", "juriste", "droit", "legal", "contentieux", "contrat"]
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in role_lower for keyword in keywords):
                return sector
        
        return "general"

    def _analyze_target_skills(self, target_role: str, job_description: Optional[str] = None, user_tier: UserTier = UserTier.FREE) -> List[str]:
        """Analyse les compétences requises pour le poste cible."""
        target_sector = self._identify_sector(target_role)
        
        # Compétences de base du secteur
        base_skills = []
        if target_sector in self.sector_skills:
            sector_data = self.sector_skills[target_sector]
            base_skills.extend(sector_data["core"])
            base_skills.extend(sector_data["trending"][:3])  # Top 3 trending
            base_skills.extend(sector_data["soft"][:2])      # Top 2 soft skills
        
        # Analyse IA de la description de poste si disponible
        if job_description:
            ai_skills = self._extract_skills_from_job_description(job_description, user_tier)
            base_skills.extend(ai_skills)
        
        # Suppression des doublons et limitation
        unique_skills = list(dict.fromkeys(base_skills))[:15]
        return unique_skills

    def _extract_skills_from_job_description(self, job_description: str, user_tier: UserTier) -> List[str]:
        """Extrait les compétences d'une description de poste via IA."""
        prompt = f"""
        Analysez cette description de poste et extrayez les compétences clés requises :
        
        {job_description}
        
        Retournez UNIQUEMENT une liste de compétences séparées par des virgules, 
        en vous concentrant sur :
        - Compétences techniques spécifiques
        - Outils et technologies mentionnés
        - Soft skills importantes
        - Certifications requises
        
        Format: compétence1, compétence2, compétence3...
        Maximum 10 compétences.
        """
        
        try:
            response = self.ai_client.generate_content(prompt=prompt, temperature=0.3, max_tokens=200, user_tier=user_tier)
            skills = [skill.strip() for skill in response.split(',')]
            return skills[:10]
        except Exception as e:
            logger.warning(f"AI skill extraction failed: {e}")
            return []

    def _identify_skill_gaps(self, current_skills: List[str], target_skills: List[str]) -> List[str]:
        """Identifie les lacunes en compétences."""
        current_lower = [skill.lower() for skill in current_skills]
        gaps = []
        
        for target_skill in target_skills:
            # Recherche exacte ou partielle
            if not any(target_skill.lower() in current.lower() or current.lower() in target_skill.lower() 
                      for current in current_lower):
                gaps.append(target_skill)
        
        return gaps

    def _assess_difficulty(self, current_sector: str, target_sector: str, skill_gaps: List[str]) -> str:
        """Évalue la difficulté de la transition."""
        # Difficulté basée sur le changement de secteur
        transition_key = (current_sector, target_sector)
        base_difficulty = self.transition_difficulty.get(transition_key, "moderate")
        
        # Ajustement basé sur le nombre de lacunes
        gap_count = len(skill_gaps)
        if gap_count <= 3:
            difficulty_modifier = 0
        elif gap_count <= 6:
            difficulty_modifier = 1
        else:
            difficulty_modifier = 2
        
        # Échelle de difficulté
        difficulty_levels = ["easy", "moderate", "challenging", "expert"]
        base_index = difficulty_levels.index(base_difficulty)
        final_index = min(len(difficulty_levels) - 1, base_index + difficulty_modifier)
        
        return difficulty_levels[final_index]

    def _calculate_success_probability(self, current_skills: List[str], 
                                     target_skills: List[str], difficulty_level: str) -> float:
        """Calcule la probabilité de succès de la reconversion."""
        # Score de base selon la difficulté
        difficulty_scores = {
            "easy": 0.85,
            "moderate": 0.70,
            "challenging": 0.55,
            "expert": 0.40
        }
        
        base_score = difficulty_scores.get(difficulty_level, 0.60)
        
        # Bonus pour les compétences existantes compatibles
        skill_overlap = len(set(s.lower() for s in current_skills) & 
                           set(s.lower() for s in target_skills))
        overlap_bonus = min(0.25, skill_overlap * 0.05)
        
        # Bonus pour l'expérience (estimé à partir du nombre de compétences actuelles)
        experience_bonus = min(0.15, len(current_skills) * 0.01)
        
        final_probability = min(0.95, base_score + overlap_bonus + experience_bonus)
        return round(final_probability, 2)

    def _generate_trajectory_steps(self, current_sector: str, target_sector: str, 
                                 skill_gaps: List[str], timeline_months: Optional[int]) -> List[TrajectoryStep]:
        """Génère les étapes du parcours de reconversion."""
        steps = []
        step_number = 1
        
        # Étape 1: Évaluation et préparation (toujours présente)
        steps.append(TrajectoryStep(
            step_number=step_number,
            title="Évaluation et Préparation",
            description="Bilan de compétences approfondi et définition des objectifs précis",
            duration_weeks=2,
            priority="critical",
            resources=["Bilan de compétences", "Entretiens avec des professionnels du secteur cible"],
            milestones=["Bilan complet réalisé", "Objectifs définis", "Plan d'action validé"],
            skills_to_develop=["auto-évaluation", "définition d'objectifs", "planification"]
        ))
        step_number += 1
        
        # Étapes de formation par groupes de compétences
        skill_groups = self._group_skills_by_learning_path(skill_gaps)
        
        for group_name, skills in skill_groups.items():
            if not skills:
                continue
                
            duration = self._estimate_learning_duration(skills)
            steps.append(TrajectoryStep(
                step_number=step_number,
                title=f"Formation - {group_name}",
                description=f"Développement des compétences en {group_name.lower()}",
                duration_weeks=duration,
                priority="critical" if step_number <= 3 else "important",
                resources=self._get_learning_resources(group_name, skills),
                milestones=[f"Maîtrise de {skill}" for skill in skills[:3]],
                skills_to_develop=skills
            ))
            step_number += 1
        
        # Étape expérience pratique
        steps.append(TrajectoryStep(
            step_number=step_number,
            title="Expérience Pratique",
            description="Acquisition d'expérience concrète dans le domaine cible",
            duration_weeks=8,
            priority="critical",
            resources=["Stage", "Projet personnel", "Freelance", "Bénévolat"],
            milestones=["Premier projet réalisé", "Portfolio constitué", "Références obtenues"],
            skills_to_develop=["application pratique", "gestion de projet", "networking"]
        ))
        step_number += 1
        
        # Étape recherche d'emploi
        steps.append(TrajectoryStep(
            step_number=step_number,
            title="Recherche d'Emploi Active",
            description="Candidatures ciblées et préparation aux entretiens",
            duration_weeks=6,
            priority="critical",
            resources=["CV optimisé", "Lettres de motivation", "Préparation entretiens", "Réseau professionnel"],
            milestones=["CV finalisé", "Candidatures envoyées", "Entretiens obtenus", "Offre reçue"],
            skills_to_develop=["recherche d'emploi", "entretien", "négociation"]
        ))
        
        return steps

    def _group_skills_by_learning_path(self, skill_gaps: List[str]) -> Dict[str, List[str]]:
        """Groupe les compétences par parcours d'apprentissage."""
        groups = {
            "Compétences Techniques": [],
            "Outils et Technologies": [],
            "Compétences Métier": [],
            "Soft Skills": []
        }
        
        technical_keywords = ["programmation", "algorithme", "base de données", "architecture", "développement"]
        tools_keywords = ["excel", "powerbi", "python", "sql", "crm", "erp", "photoshop"]
        business_keywords = ["gestion", "analyse", "stratégie", "marketing", "finance", "commercial"]
        soft_keywords = ["leadership", "communication", "négociation", "créativité", "organisation"]
        
        for skill in skill_gaps:
            skill_lower = skill.lower()
            
            if any(keyword in skill_lower for keyword in technical_keywords):
                groups["Compétences Techniques"].append(skill)
            elif any(keyword in skill_lower for keyword in tools_keywords):
                groups["Outils et Technologies"].append(skill)
            elif any(keyword in skill_lower for keyword in business_keywords):
                groups["Compétences Métier"].append(skill)
            elif any(keyword in skill_lower for keyword in soft_keywords):
                groups["Soft Skills"].append(skill)
            else:
                groups["Compétences Métier"].append(skill)  # Par défaut
        
        return {k: v for k, v in groups.items() if v}  # Supprimer les groupes vides

    def _estimate_learning_duration(self, skills: List[str]) -> int:
        """Estime la durée d'apprentissage en semaines."""
        base_duration_per_skill = 3  # 3 semaines par compétence
        skill_count = len(skills)
        
        # Efficacité d'apprentissage en groupe
        if skill_count == 1:
            return base_duration_per_skill
        elif skill_count <= 3:
            return skill_count * 2  # Synergie d'apprentissage
        else:
            return min(12, skill_count * 2)  # Plafond à 12 semaines

    def _get_learning_resources(self, group_name: str, skills: List[str]) -> List[str]:
        """Obtient les ressources d'apprentissage pour un groupe de compétences."""
        resource_templates = {
            "Compétences Techniques": ["Cours en ligne spécialisés", "Documentation officielle", "Projets pratiques"],
            "Outils et Technologies": ["Tutoriels officiels", "Certifications", "Hands-on labs"],
            "Compétences Métier": ["Formation professionnelle", "Livres spécialisés", "Webinaires sectoriels"],
            "Soft Skills": ["Coaching", "Ateliers pratiques", "Lectures spécialisées"]
        }
        
        base_resources = resource_templates.get(group_name, ["Formation générale", "Ressources en ligne"])
        
        # Personnalisation par compétence
        specific_resources = []
        for skill in skills[:2]:  # Top 2 skills
            specific_resources.append(f"Formation spécialisée en {skill}")
        
        return base_resources + specific_resources

    def _estimate_duration(self, difficulty_level: str, gap_count: int) -> int:
        """Estime la durée totale de la reconversion en mois."""
        base_durations = {
            "easy": 6,
            "moderate": 9,
            "challenging": 12,
            "expert": 18
        }
        
        base_duration = base_durations.get(difficulty_level, 9)
        
        # Ajustement basé sur le nombre de lacunes
        gap_adjustment = min(6, gap_count * 0.5)
        
        return int(base_duration + gap_adjustment)

    def _get_recommended_resources(self, target_sector: str, skill_gaps: List[str]) -> List[Dict[str, str]]:
        """Obtient les ressources recommandées par secteur."""
        sector_resources = {
            "tech": [
                {"type": "course", "name": "OpenClassrooms - Développeur", "url": "https://openclassrooms.com"},
                {"type": "certification", "name": "Certifications AWS/Azure", "url": "https://aws.amazon.com/certification/"},
                {"type": "platform", "name": "GitHub pour portfolio", "url": "https://github.com"}
            ],
            "marketing": [
                {"type": "course", "name": "Google Digital Marketing", "url": "https://learndigital.withgoogle.com"},
                {"type": "certification", "name": "HubSpot Marketing", "url": "https://academy.hubspot.com"},
                {"type": "book", "name": "Mercator - Marketing", "url": ""}
            ],
            "finance": [
                {"type": "certification", "name": "CFA Institute", "url": "https://www.cfainstitute.org"},
                {"type": "course", "name": "Formation comptabilité CNAM", "url": "https://www.cnam.fr"},
                {"type": "book", "name": "Analyse financière", "url": ""}
            ]
        }
        
        return sector_resources.get(target_sector, [
            {"type": "course", "name": "Formation en ligne généraliste", "url": ""},
            {"type": "book", "name": "Ressources spécialisées secteur", "url": ""},
            {"type": "networking", "name": "Événements professionnels", "url": ""}
        ])

    def _get_industry_insights(self, target_sector: str) -> Dict[str, any]:
        """Obtient les insights sectoriels."""
        insights = {
            "tech": {
                "growth_rate": "forte croissance",
                "job_demand": "très élevée",
                "avg_salary_range": "35-80k€",
                "key_trends": ["IA/ML", "Cloud", "Cybersécurité", "DevOps"],
                "entry_barriers": "Portfolio technique requis",
                "remote_friendly": True
            },
            "marketing": {
                "growth_rate": "croissance modérée",
                "job_demand": "élevée",
                "avg_salary_range": "30-60k€", 
                "key_trends": ["Marketing digital", "Data analytics", "Automation"],
                "entry_barriers": "Expérience digitale appréciée",
                "remote_friendly": True
            }
        }
        
        return insights.get(target_sector, {
            "growth_rate": "variable",
            "job_demand": "modérée",
            "avg_salary_range": "Variable selon expérience",
            "key_trends": ["Transformation digitale"],
            "entry_barriers": "Expérience sectorielle requise",
            "remote_friendly": False
        })

    def update_plan_progress(self, plan: ReconversionPlan, 
                           completed_steps: List[int]) -> ReconversionPlan:
        """Met à jour le progrès d'un plan de reconversion."""
        try:
            # Marquer les étapes comme complétées
            for step in plan.trajectory_steps:
                if step.step_number in completed_steps:
                    step.priority = "completed"
            
            # Recalculer la probabilité de succès basée sur le progrès
            completion_rate = len(completed_steps) / len(plan.trajectory_steps)
            progress_bonus = completion_rate * 0.15
            plan.success_probability = min(0.95, plan.success_probability + progress_bonus)
            
            # Mettre à jour la date
            plan.last_updated = datetime.now()
            
            logger.info(f"Plan updated - Progress: {completion_rate:.1%}")
            return plan
            
        except Exception as e:
            logger.error(f"Error updating plan progress: {e}")
            return plan

    def _get_fallback_plan(self, user_id: str, current_role: str, target_role: str, is_premium_feature: bool = False) -> ReconversionPlan:
        """Plan de secours en cas d'erreur."""
        if is_premium_feature:
            return ReconversionPlan(
                user_id=user_id,
                current_role=current_role,
                target_role=target_role,
                current_skills=["Fonctionnalité Premium"],
                target_skills=["N/A"],
                skill_gaps=["N/A"],
                trajectory_steps=[
                    TrajectoryStep(
                        step_number=1,
                        title="Accès Premium Requis",
                        description="Cette fonctionnalité est réservée aux utilisateurs Premium. Passez Premium pour générer votre plan de reconversion personnalisé.",
                        duration_weeks=0,
                        priority="critical",
                        resources=["Passez Premium"],
                        milestones=["Débloquez votre potentiel"],
                        skills_to_develop=["N/A"]
                    )
                ],
                estimated_duration_months=0,
                difficulty_level="N/A",
                success_probability=0.0,
                recommended_resources=[{"type": "info", "name": "Passez Premium pour débloquer", "url": ""}],
                industry_insights={"note": "Fonctionnalité Premium"},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
        return ReconversionPlan(
            user_id=user_id,
            current_role=current_role,
            target_role=target_role,
            current_skills=["Compétences actuelles à analyser"],
            target_skills=["Compétences cibles à définir"],
            skill_gaps=["Analyse détaillée requise"],
            trajectory_steps=[
                TrajectoryStep(
                    step_number=1,
                    title="Analyse Approfondie",
                    description="Réaliser une analyse détaillée de votre situation",
                    duration_weeks=2,
                    priority="critical",
                    resources=["Bilan de compétences", "Conseil en évolution professionnelle"],
                    milestones=["Bilan réalisé"],
                    skills_to_develop=["auto-évaluation"]
                )
            ],
            estimated_duration_months=12,
            difficulty_level="moderate",
            success_probability=0.60,
            recommended_resources=[{"type": "conseil", "name": "Accompagnement personnalisé", "url": ""}],
            industry_insights={"note": "Analyse personnalisée requise"},
            created_at=datetime.now(),
            last_updated=datetime.now()
        )