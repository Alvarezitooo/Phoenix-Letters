"""Gestionnaire d'audit RGPD pour Phoenix Letters."""
import logging
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re


class DataCategory(Enum):
    """Catégories de données RGPD."""
    PERSONAL_IDENTIFIABLE = "personal_identifiable"  # Nom, email, téléphone
    PROFESSIONAL = "professional"  # CV, expérience, compétences
    TECHNICAL = "technical"  # IP, cookies, logs
    USAGE = "usage"  # Analytics, comportement
    SENSITIVE = "sensitive"  # Données sensibles Art.9 RGPD


class LegalBasis(Enum):
    """Bases légales RGPD."""
    CONSENT = "consent"  # Consentement Art.6(1)(a)
    CONTRACT = "contract"  # Exécution contrat Art.6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation"  # Obligation légale Art.6(1)(c)
    VITAL_INTERESTS = "vital_interests"  # Intérêts vitaux Art.6(1)(d)
    PUBLIC_TASK = "public_task"  # Mission service public Art.6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Intérêts légitimes Art.6(1)(f)


@dataclass
class DataProcessingActivity:
    """Activité de traitement des données."""
    activity_id: str
    name: str
    description: str
    data_categories: List[DataCategory]
    legal_basis: LegalBasis
    purposes: List[str]
    data_subjects: List[str]  # "users", "prospects", "employees"
    retention_period: str
    recipients: List[str]  # Qui a accès aux données
    international_transfers: bool
    security_measures: List[str]
    automated_decision_making: bool
    consent_mechanism: Optional[str] = None
    opt_out_mechanism: Optional[str] = None


@dataclass
class RGPDComplianceIssue:
    """Issue de conformité RGPD."""
    severity: str  # "low", "medium", "high", "critical"
    category: str
    article: str  # Article RGPD concerné
    description: str
    recommendation: str
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    deadline: Optional[str] = None  # Délai recommandé pour correction


@dataclass
class RGPDAuditReport:
    """Rapport d'audit RGPD complet."""
    audit_timestamp: str
    compliance_score: float  # 0.0 - 100.0
    processing_activities: List[DataProcessingActivity]
    compliance_issues: List[RGPDComplianceIssue]
    rights_implementation: Dict[str, bool]
    privacy_by_design_score: float
    documentation_completeness: float
    recommendations: List[str]
    next_audit_date: str


class RGPDAuditManager:
    """Gestionnaire d'audit RGPD pour Phoenix Letters."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Activités de traitement Phoenix Letters
        self.processing_activities = self._init_processing_activities()
        
        # Patterns de détection données personnelles
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'(?:\+33|0)[1-9](?:[0-9]{8})',
            "name": r'(?i)(nom|prénom|name|firstname|lastname)[:=]\s*["\']([^"\']+)["\']',
            "address": r'(?i)(adresse|address)[:=]\s*["\']([^"\']+)["\']',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "user_id": r'(?i)user[_-]?id[:=]\s*["\']?([^"\']+)["\']?'
        }
        
        # Droits RGPD à vérifier
        self.gdpr_rights = [
            "right_to_information",      # Art.13-14
            "right_of_access",          # Art.15
            "right_to_rectification",   # Art.16
            "right_to_erasure",         # Art.17
            "right_to_portability",     # Art.20
            "right_to_object",          # Art.21
            "right_to_restrict",        # Art.18
            "automated_decision_rights"  # Art.22
        ]
    
    def _init_processing_activities(self) -> List[DataProcessingActivity]:
        """Initialise les activités de traitement Phoenix Letters."""
        
        return [
            # Génération de lettres de motivation
            DataProcessingActivity(
                activity_id="letter_generation",
                name="Génération de lettres de motivation",
                description="Traitement des CV et données utilisateur pour générer lettres personnalisées",
                data_categories=[
                    DataCategory.PERSONAL_IDENTIFIABLE,
                    DataCategory.PROFESSIONAL
                ],
                legal_basis=LegalBasis.CONTRACT,
                purposes=[
                    "Génération lettres motivation personnalisées",
                    "Amélioration service IA",
                    "Support utilisateur"
                ],
                data_subjects=["users", "prospects"],
                retention_period="24 mois après dernière utilisation",
                recipients=["Équipe technique Phoenix", "Prestataires IA (Google Gemini)"],
                international_transfers=True,  # Google Gemini
                security_measures=[
                    "Chiffrement données transit/repos",
                    "Authentification utilisateur",
                    "Logs d'accès",
                    "Anonymisation temporaire"
                ],
                automated_decision_making=False,
                consent_mechanism="Acceptation CGU lors inscription",
                opt_out_mechanism="Suppression compte utilisateur"
            ),
            
            # Analytics et amélioration produit
            DataProcessingActivity(
                activity_id="analytics_improvement",
                name="Analytics et amélioration produit",
                description="Collecte données usage pour améliorer expérience utilisateur",
                data_categories=[
                    DataCategory.USAGE,
                    DataCategory.TECHNICAL
                ],
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                purposes=[
                    "Amélioration interface utilisateur",
                    "Optimisation performance",
                    "Détection bugs"
                ],
                data_subjects=["users"],
                retention_period="12 mois",
                recipients=["Équipe produit Phoenix"],
                international_transfers=False,
                security_measures=[
                    "Anonymisation données",
                    "Agrégation statistiques",
                    "Accès restreint équipe"
                ],
                automated_decision_making=False,
                consent_mechanism="Bannière cookies",
                opt_out_mechanism="Paramètres cookies"
            ),
            
            # Marketing et communication
            DataProcessingActivity(
                activity_id="marketing_communication",
                name="Marketing et communication",
                description="Envoi newsletters et communications marketing",
                data_categories=[
                    DataCategory.PERSONAL_IDENTIFIABLE,
                    DataCategory.PROFESSIONAL
                ],
                legal_basis=LegalBasis.CONSENT,
                purposes=[
                    "Envoi newsletter Phoenix Letters",
                    "Communications produit",
                    "Offres personnalisées"
                ],
                data_subjects=["users", "prospects"],
                retention_period="Jusqu'à désinscription + 3 ans",
                recipients=["Équipe marketing Phoenix"],
                international_transfers=False,
                security_measures=[
                    "Liste opt-in explicite",
                    "Lien désinscription",
                    "Chiffrement base emails"
                ],
                automated_decision_making=True,  # Personnalisation
                consent_mechanism="Case à cocher newsletter",
                opt_out_mechanism="Lien désinscription email"
            )
        ]
    
    def conduct_full_audit(self, project_path: str) -> RGPDAuditReport:
        """
        Conduit audit RGPD complet du projet.
        
        Args:
            project_path: Chemin du projet Phoenix Letters
        Returns:
            RGPDAuditReport complet
        """
        
        self.logger.info("Starting comprehensive GDPR audit")
        
        # 1. Audit des activités de traitement
        processing_activities = self.processing_activities
        
        # 2. Détection problèmes conformité
        compliance_issues = self._detect_compliance_issues(project_path)
        
        # 3. Vérification implémentation droits
        rights_implementation = self._audit_rights_implementation(project_path)
        
        # 4. Score Privacy by Design
        privacy_score = self._calculate_privacy_by_design_score(project_path)
        
        # 5. Complétude documentation
        doc_completeness = self._assess_documentation_completeness(project_path)
        
        # 6. Score conformité global
        compliance_score = self._calculate_compliance_score(
            compliance_issues, rights_implementation, privacy_score, doc_completeness
        )
        
        # 7. Recommandations
        recommendations = self._generate_rgpd_recommendations(
            compliance_issues, rights_implementation
        )
        
        # 8. Prochaine date audit
        next_audit = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        
        report = RGPDAuditReport(
            audit_timestamp=datetime.now().isoformat(),
            compliance_score=compliance_score,
            processing_activities=processing_activities,
            compliance_issues=compliance_issues,
            rights_implementation=rights_implementation,
            privacy_by_design_score=privacy_score,
            documentation_completeness=doc_completeness,
            recommendations=recommendations,
            next_audit_date=next_audit
        )
        
        self.logger.info(f"GDPR audit completed. Compliance score: {compliance_score:.1f}%")
        
        return report
    
    def _detect_compliance_issues(self, project_path: str) -> List[RGPDComplianceIssue]:
        """Détecte problèmes de conformité RGPD."""
        
        issues = []
        
        # Scanner fichiers pour données personnelles non protégées
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith(('.py', '.js', '.json', '.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    issues.extend(self._scan_file_for_rgpd_issues(file_path))
        
        # Vérifications spécifiques
        issues.extend(self._check_consent_mechanisms(project_path))
        issues.extend(self._check_data_retention_policies(project_path))
        issues.extend(self._check_international_transfers(project_path))
        issues.extend(self._check_automated_decision_making(project_path))
        
        return issues
    
    def _scan_file_for_rgpd_issues(self, file_path: str) -> List[RGPDComplianceIssue]:
        """Scanne fichier pour issues RGPD."""
        
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Détecter données personnelles hardcodées
            for pii_type, pattern in self.pii_patterns.items():
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Ignorer si dans commentaires ou exemples
                    line_content = lines[line_num - 1]
                    if any(marker in line_content for marker in ['#', '//', '"""', "'''"]):
                        continue
                    
                    issues.append(RGPDComplianceIssue(
                        severity="high",
                        category="hardcoded_personal_data",
                        article="Art.5 RGPD (Minimisation)",
                        description=f"Données personnelles potentielles détectées: {pii_type}",
                        recommendation="Anonymiser ou chiffrer données personnelles",
                        file_path=file_path,
                        code_snippet=line_content.strip(),
                        deadline="15 jours"
                    ))
            
            # Détecter logging de données personnelles
            if re.search(r'(?i)log.*(?:email|nom|prénom|adresse)', content):
                issues.append(RGPDComplianceIssue(
                    severity="medium",
                    category="personal_data_logging",
                    article="Art.5 RGPD (Licéité)",
                    description="Logging potentiel de données personnelles",
                    recommendation="Anonymiser logs ou éviter logging données personnelles",
                    file_path=file_path,
                    deadline="30 jours"
                ))
            
            # Détecter absence chiffrement
            if 'password' in content.lower() and 'hash' not in content.lower():
                issues.append(RGPDComplianceIssue(
                    severity="critical",
                    category="unencrypted_passwords",
                    article="Art.32 RGPD (Sécurité)",
                    description="Mots de passe potentiellement non chiffrés",
                    recommendation="Implémenter hachage sécurisé (bcrypt, argon2)",
                    file_path=file_path,
                    deadline="7 jours"
                ))
                
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
        
        return issues
    
    def _check_consent_mechanisms(self, project_path: str) -> List[RGPDComplianceIssue]:
        """Vérifie mécanismes de consentement."""
        
        issues = []
        
        # Rechercher implémentation consentement
        consent_found = False
        
        # Scanner pour patterns de consentement
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if re.search(r'(?i)(consent|consentement|newsletter.*opt)', content):
                            consent_found = True
                            break
                    except:
                        continue
        
        if not consent_found:
            issues.append(RGPDComplianceIssue(
                severity="high",
                category="missing_consent_mechanism",
                article="Art.6-7 RGPD (Base légale)",
                description="Aucun mécanisme de consentement détecté",
                recommendation="Implémenter système consentement explicite",
                deadline="30 jours"
            ))
        
        return issues
    
    def _check_data_retention_policies(self, project_path: str) -> List[RGPDComplianceIssue]:
        """Vérifie politiques de rétention."""
        
        issues = []
        
        # Rechercher implémentation rétention
        retention_found = False
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if re.search(r'(?i)(retention|delete.*after|expir)', content):
                            retention_found = True
                            break
                    except:
                        continue
        
        if not retention_found:
            issues.append(RGPDComplianceIssue(
                severity="medium",
                category="missing_retention_policy",
                article="Art.5 RGPD (Limitation conservation)",
                description="Aucune politique de rétention détectée",
                recommendation="Implémenter suppression automatique données expirées",
                deadline="60 jours"
            ))
        
        return issues
    
    def _check_international_transfers(self, project_path: str) -> List[RGPDComplianceIssue]:
        """Vérifie transferts internationaux."""
        
        issues = []
        
        # Détecter APIs tierces (Google, OpenAI, etc.)
        international_apis = {
            'google': 'États-Unis',
            'openai': 'États-Unis', 
            'anthropic': 'États-Unis',
            'aws': 'États-Unis'
        }
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for api, country in international_apis.items():
                            if api in content.lower():
                                issues.append(RGPDComplianceIssue(
                                    severity="medium",
                                    category="international_transfer",
                                    article="Art.44-49 RGPD (Transferts)",
                                    description=f"Transfert international vers {country} via {api}",
                                    recommendation="Vérifier mécanismes transfert (décision adéquation, clauses contractuelles)",
                                    file_path=file_path,
                                    deadline="45 jours"
                                ))
                                break
                    except:
                        continue
        
        return issues
    
    def _check_automated_decision_making(self, project_path: str) -> List[RGPDComplianceIssue]:
        """Vérifie prise de décision automatisée."""
        
        issues = []
        
        # Détecter IA/algorithmes de décision
        decision_patterns = [
            r'(?i)(decision|décision).*auto',
            r'(?i)(recommend|recommand).*algorithm',
            r'(?i)(score|scoring).*user',
            r'(?i)machine.*learning.*decision'
        ]
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern in decision_patterns:
                            if re.search(pattern, content):
                                issues.append(RGPDComplianceIssue(
                                    severity="medium",
                                    category="automated_decision_making",
                                    article="Art.22 RGPD (Décision automatisée)",
                                    description="Prise de décision automatisée détectée",
                                    recommendation="Informer utilisateurs et permettre intervention humaine",
                                    file_path=file_path,
                                    deadline="30 jours"
                                ))
                                break
                    except:
                        continue
        
        return issues
    
    def _audit_rights_implementation(self, project_path: str) -> Dict[str, bool]:
        """Audite implémentation des droits RGPD."""
        
        rights_status = {}
        
        for right in self.gdpr_rights:
            rights_status[right] = self._check_right_implementation(project_path, right)
        
        return rights_status
    
    def _check_right_implementation(self, project_path: str, right: str) -> bool:
        """Vérifie implémentation d'un droit spécifique."""
        
        # Patterns par droit
        right_patterns = {
            "right_to_information": [r'(?i)(privacy.*policy|politique.*confidentialité)', r'(?i)information.*collect'],
            "right_of_access": [r'(?i)(download.*data|export.*data|mes.*données)'],
            "right_to_rectification": [r'(?i)(update.*profile|modifier.*profil)'],
            "right_to_erasure": [r'(?i)(delete.*account|supprimer.*compte)', r'(?i)right.*forgotten'],
            "right_to_portability": [r'(?i)(export.*data|portabilité)'],
            "right_to_object": [r'(?i)(opt.*out|objection|opposition)'],
            "right_to_restrict": [r'(?i)(restrict.*processing|limiter.*traitement)'],
            "automated_decision_rights": [r'(?i)(human.*intervention|intervention.*humaine)']
        }
        
        patterns = right_patterns.get(right, [])
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern in patterns:
                            if re.search(pattern, content):
                                return True
                    except:
                        continue
        
        return False
    
    def _calculate_privacy_by_design_score(self, project_path: str) -> float:
        """Calcule score Privacy by Design."""
        
        score = 0.0
        max_score = 7.0  # 7 principes Privacy by Design
        
        # 1. Proactif plutôt que réactif
        if self._check_proactive_measures(project_path):
            score += 1.0
            
        # 2. Sécurité par défaut
        if self._check_default_security(project_path):
            score += 1.0
            
        # 3. Sécurité intégrée à la conception
        if self._check_built_in_security(project_path):
            score += 1.0
            
        # 4. Fonctionnalité complète - Somme positive
        if self._check_full_functionality(project_path):
            score += 1.0
            
        # 5. Sécurité de bout en bout
        if self._check_end_to_end_security(project_path):
            score += 1.0
            
        # 6. Visibilité et transparence
        if self._check_visibility_transparency(project_path):
            score += 1.0
            
        # 7. Respect de la vie privée
        if self._check_privacy_respect(project_path):
            score += 1.0
        
        return (score / max_score) * 100.0
    
    def _check_proactive_measures(self, project_path: str) -> bool:
        """Vérifie mesures proactives."""
        # Rechercher validation d'entrée, sanitisation, etc.
        proactive_patterns = [r'(?i)validat', r'(?i)sanitiz', r'(?i)clean']
        return self._search_patterns_in_project(project_path, proactive_patterns)
    
    def _check_default_security(self, project_path: str) -> bool:
        """Vérifie sécurité par défaut."""
        security_patterns = [r'(?i)encrypt', r'(?i)hash', r'(?i)secure']
        return self._search_patterns_in_project(project_path, security_patterns)
    
    def _check_built_in_security(self, project_path: str) -> bool:
        """Vérifie sécurité intégrée."""
        builtin_patterns = [r'(?i)authentication', r'(?i)authorization', r'(?i)csrf']
        return self._search_patterns_in_project(project_path, builtin_patterns)
    
    def _check_full_functionality(self, project_path: str) -> bool:
        """Vérifie fonctionnalité complète."""
        # Vérifier que sécurité n'empêche pas fonctionnalités
        return True  # Simplification pour démo
    
    def _check_end_to_end_security(self, project_path: str) -> bool:
        """Vérifie sécurité bout en bout."""
        e2e_patterns = [r'(?i)https', r'(?i)tls', r'(?i)ssl']
        return self._search_patterns_in_project(project_path, e2e_patterns)
    
    def _check_visibility_transparency(self, project_path: str) -> bool:
        """Vérifie visibilité et transparence."""
        transparency_patterns = [r'(?i)privacy.*policy', r'(?i)log', r'(?i)audit']
        return self._search_patterns_in_project(project_path, transparency_patterns)
    
    def _check_privacy_respect(self, project_path: str) -> bool:
        """Vérifie respect vie privée."""
        privacy_patterns = [r'(?i)anonymiz', r'(?i)pseudonymiz', r'(?i)minimal']
        return self._search_patterns_in_project(project_path, privacy_patterns)
    
    def _search_patterns_in_project(self, project_path: str, patterns: List[str]) -> bool:
        """Recherche patterns dans le projet."""
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern in patterns:
                            if re.search(pattern, content):
                                return True
                    except:
                        continue
        return False
    
    def _assess_documentation_completeness(self, project_path: str) -> float:
        """Évalue complétude documentation RGPD."""
        
        required_docs = [
            "privacy_policy", "cookies_policy", "terms_of_service",
            "data_processing_register", "dpo_contact", "breach_procedure"
        ]
        
        found_docs = 0
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(('.md', '.txt', '.pdf', '.html')):
                    file_lower = file.lower()
                    for doc in required_docs:
                        if doc.replace('_', '') in file_lower.replace('_', ''):
                            found_docs += 1
                            break
        
        return (found_docs / len(required_docs)) * 100.0
    
    def _calculate_compliance_score(
        self,
        issues: List[RGPDComplianceIssue],
        rights: Dict[str, bool],
        privacy_score: float,
        doc_score: float
    ) -> float:
        """Calcule score de conformité global."""
        
        # Pénalités par sévérité
        penalties = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        
        total_penalty = sum(penalties.get(issue.severity, 0) for issue in issues)
        rights_score = (sum(rights.values()) / len(rights)) * 100.0
        
        # Score pondéré
        compliance_score = (
            (100 - min(total_penalty, 80)) * 0.4 +  # 40% issues
            rights_score * 0.3 +                    # 30% droits
            privacy_score * 0.2 +                   # 20% privacy by design
            doc_score * 0.1                         # 10% documentation
        )
        
        return max(0.0, min(100.0, compliance_score))
    
    def _generate_rgpd_recommendations(
        self,
        issues: List[RGPDComplianceIssue],
        rights: Dict[str, bool]
    ) -> List[str]:
        """Génère recommandations RGPD."""
        
        recommendations = []
        
        # Recommandations par sévérité
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        
        if critical_issues:
            recommendations.append("🚨 URGENT: Corriger immédiatement les issues critiques RGPD")
        
        if high_issues:
            recommendations.append("⚠️ PRIORITÉ: Traiter les issues hautes sous 15 jours")
        
        # Recommandations par droits manquants
        missing_rights = [right for right, implemented in rights.items() if not implemented]
        
        if "right_to_erasure" in missing_rights:
            recommendations.append("🗑️ Implémenter droit à l'effacement (suppression compte)")
        
        if "right_of_access" in missing_rights:
            recommendations.append("📊 Implémenter droit d'accès (export données)")
        
        if "right_to_information" in missing_rights:
            recommendations.append("📋 Créer politique de confidentialité complète")
        
        # Recommandations générales
        recommendations.extend([
            "📝 Tenir registre des activités de traitement à jour",
            "🔒 Implémenter Privacy by Design dans nouveaux développements",
            "👨‍💼 Désigner DPO ou référent RGPD",
            "🔄 Planifier audits RGPD réguliers (6 mois)",
            "📚 Former équipe aux obligations RGPD"
        ])
        
        return recommendations
    
    def export_rgpd_report(self, report: RGPDAuditReport, output_file: str) -> None:
        """Exporte rapport RGPD."""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"GDPR audit report exported to {output_file}")
    
    def generate_privacy_policy_template(self) -> str:
        """Génère template politique de confidentialité."""
        
        return """
# Politique de Confidentialité - Phoenix Letters

## 1. Responsable du traitement
Phoenix Letters, [adresse]
Contact DPO: privacy@phoenix-letters.fr

## 2. Données collectées et finalités

### Génération de lettres de motivation
- **Données**: CV, informations professionnelles, préférences
- **Base légale**: Exécution du contrat (Art.6.1.b RGPD)
- **Finalité**: Génération lettres personnalisées
- **Conservation**: 24 mois après dernière utilisation

### Analytics et amélioration
- **Données**: Données d'usage, techniques
- **Base légale**: Intérêts légitimes (Art.6.1.f RGPD)
- **Finalité**: Amélioration produit
- **Conservation**: 12 mois

## 3. Destinataires des données
- Équipe technique Phoenix Letters
- Prestataires IA (Google Gemini) - transfert États-Unis

## 4. Vos droits
- Droit d'accès (Art.15)
- Droit de rectification (Art.16)  
- Droit à l'effacement (Art.17)
- Droit à la portabilité (Art.20)
- Droit d'opposition (Art.21)

Contact: privacy@phoenix-letters.fr

## 5. Sécurité
Chiffrement, authentification, logs d'accès, anonymisation.

## 6. Cookies
Utilisation cookies analytics. Paramétrage possible.

Dernière mise à jour: [DATE]
        """.strip()


if __name__ == "__main__":
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="Phoenix Letters GDPR Audit")
    parser.add_argument("project_path", help="Path to Phoenix Letters project")
    parser.add_argument("--output", "-o", default="rgpd_audit_report.json", help="Output file")
    
    args = parser.parse_args()
    
    auditor = RGPDAuditManager()
    report = auditor.conduct_full_audit(args.project_path)
    
    auditor.export_rgpd_report(report, args.output)
    
    print(f"GDPR audit completed. Compliance score: {report.compliance_score:.1f}%")
    print(f"Issues found: {len(report.compliance_issues)}")
    print(f"Rights implemented: {sum(report.rights_implementation.values())}/{len(report.rights_implementation)}")