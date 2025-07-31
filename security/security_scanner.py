"""Scanner de sécurité personnalisé pour Phoenix Letters."""
import os
import re
import json
import ast
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging


@dataclass
class SecurityIssue:
    """Issue de sécurité détectée."""
    severity: str  # "low", "medium", "high", "critical"
    category: str  # "hardcoded_secret", "sql_injection", "path_traversal", etc.
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    recommendation: str
    confidence: float  # 0.0 - 1.0


@dataclass
class SecurityReport:
    """Rapport de sécurité complet."""
    scan_timestamp: str
    total_files_scanned: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[SecurityIssue]
    recommendations: List[str]
    compliance_status: Dict[str, bool]


class PhoenixSecurityScanner:
    """Scanner de sécurité spécialisé pour Phoenix Letters."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Patterns de sécurité spécifiques
        self.security_patterns = {
            # Secrets hardcodés
            "hardcoded_secrets": [
                (r'(?i)(api[_-]?key|secret[_-]?key|password|token)\s*[=:]\s*["\']([^"\']{8,})["\']', "high"),
                (r'(?i)google[_-]?api[_-]?key\s*[=:]\s*["\']([^"\']{20,})["\']', "critical"),
                (r'(?i)openai[_-]?api[_-]?key\s*[=:]\s*["\']([^"\']{20,})["\']', "critical"),
                (r'(?i)(gemini|claude)[_-]?api[_-]?key\s*[=:]\s*["\']([^"\']{20,})["\']', "critical"),
            ],
            
            # Injections SQL/NoSQL
            "sql_injection": [
                (r'(?i)execute\s*\(\s*["\'].*\+.*["\']', "high"),
                (r'(?i)query\s*\(\s*["\'].*%s.*["\']', "high"),
                (r'(?i)\.format\s*\(.*sql.*\)', "medium"),
            ],
            
            # Path Traversal
            "path_traversal": [
                (r'open\s*\(\s*.*\+.*\)', "medium"),
                (r'os\.path\.join\s*\(.*input.*\)', "medium"),
                (r'\.\./', "low"),
            ],
            
            # Désérialisation non sécurisée
            "unsafe_deserialization": [
                (r'pickle\.load', "high"),
                (r'yaml\.load\s*\((?!.*Loader=yaml\.SafeLoader)', "high"),
                (r'eval\s*\(', "critical"),
                (r'exec\s*\(', "critical"),
            ],
            
            # Headers de sécurité manquants
            "security_headers": [
                (r'(?i)x-frame-options', "info"),
                (r'(?i)content-security-policy', "info"),
                (r'(?i)x-content-type-options', "info"),
            ],
            
            # Validation d'entrée insuffisante
            "input_validation": [
                (r'request\.args\.get\s*\([^,]+\)(?!\s*or\s)', "medium"),
                (r'request\.form\.get\s*\([^,]+\)(?!\s*or\s)', "medium"),
                (r'st\.text_input\s*\([^,]+\)(?!\s*,.*max_chars)', "low"),
            ],
            
            # Logging sensible
            "sensitive_logging": [
                (r'(?i)log.*(?:password|token|key|secret)', "medium"),
                (r'(?i)print.*(?:password|token|key|secret)', "medium"),
            ],
            
            # Gestion d'erreurs
            "error_handling": [
                (r'except\s*:', "low"),
                (r'except\s+Exception\s*:', "low"),
                (r'pass\s*$', "low"),
            ]
        }
        
        # Fichiers sensibles à scanner en priorité
        self.sensitive_files = [
            "config", "settings", "env", "auth", "security", 
            "database", "api", "client", "service"
        ]
        
        # Extensions à scanner
        self.scan_extensions = {".py", ".yaml", ".yml", ".json", ".env", ".cfg", ".ini"}
    
    def scan_directory(self, directory_path: str) -> SecurityReport:
        """
        Lance scan sécurité complet sur répertoire.
        
        Args:
            directory_path: Chemin du répertoire à scanner
        Returns:
            SecurityReport complet
        """
        
        self.logger.info(f"Starting security scan of {directory_path}")
        
        all_issues = []
        files_scanned = 0
        
        # Scanner tous les fichiers
        for root, dirs, files in os.walk(directory_path):
            # Ignorer certains répertoires
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_scan_file(file_path):
                    issues = self._scan_file(file_path)
                    all_issues.extend(issues)
                    files_scanned += 1
        
        # Analyser issues par sévérité
        issues_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0, "info": 0}
        for issue in all_issues:
            issues_by_severity[issue.severity] += 1
        
        # Générer recommandations
        recommendations = self._generate_recommendations(all_issues)
        
        # Évaluer compliance
        compliance_status = self._evaluate_compliance(all_issues)
        
        report = SecurityReport(
            scan_timestamp=str(datetime.now()),
            total_files_scanned=files_scanned,
            total_issues=len(all_issues),
            issues_by_severity=issues_by_severity,
            issues=all_issues,
            recommendations=recommendations,
            compliance_status=compliance_status
        )
        
        self.logger.info(f"Security scan completed: {len(all_issues)} issues found")
        
        return report
    
    def _should_scan_file(self, file_path: str) -> bool:
        """Détermine si fichier doit être scanné."""
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.scan_extensions:
            return False
        
        # Ignorer fichiers temporaires
        if any(temp in file_path for temp in ['.pyc', '__pycache__', '.git', '.DS_Store']):
            return False
        
        return True
    
    def _scan_file(self, file_path: str) -> List[SecurityIssue]:
        """Scanne fichier individuel pour issues sécurité."""
        
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        
            # Scanner patterns par catégorie
            for category, patterns in self.security_patterns.items():
                for pattern, severity in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Extraire snippet de code
                        start_line = max(0, line_num - 2)
                        end_line = min(len(lines), line_num + 1)
                        code_snippet = '\n'.join(lines[start_line:end_line])
                        
                        issue = SecurityIssue(
                            severity=severity,
                            category=category,
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=code_snippet,
                            description=self._get_issue_description(category, match.group()),
                            recommendation=self._get_recommendation(category),
                            confidence=self._calculate_confidence(category, match.group())
                        )
                        
                        issues.append(issue)
            
            # Scans spécialisés selon type de fichier
            if file_path.endswith('.py'):
                issues.extend(self._scan_python_specific(file_path, content))
            elif file_path.endswith(('.yaml', '.yml')):
                issues.extend(self._scan_yaml_specific(file_path, content))
                
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
        
        return issues
    
    def _scan_python_specific(self, file_path: str, content: str) -> List[SecurityIssue]:
        """Scans spécifiques aux fichiers Python."""
        
        issues = []
        
        try:
            # Analyser AST pour détections avancées
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Détection imports dangereux
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['pickle', 'marshal', 'shelve']:
                            issues.append(SecurityIssue(
                                severity="medium",
                                category="dangerous_import",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet=f"import {alias.name}",
                                description=f"Import potentiellement dangereux: {alias.name}",
                                recommendation="Utiliser des alternatives sécurisées comme json",
                                confidence=0.8
                            ))
                
                # Détection debug mode
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (isinstance(target, ast.Name) and 
                            target.id.lower() in ['debug', 'development'] and
                            isinstance(node.value, ast.Constant) and
                            node.value.value is True):
                            
                            issues.append(SecurityIssue(
                                severity="medium",
                                category="debug_mode",
                                file_path=file_path,
                                line_number=node.lineno,
                                code_snippet="DEBUG = True",
                                description="Mode debug activé en production",
                                recommendation="Désactiver debug en production",
                                confidence=0.9
                            ))
                            
        except SyntaxError:
            # Fichier Python invalide
            pass
        except Exception as e:
            self.logger.warning(f"AST analysis failed for {file_path}: {e}")
        
        return issues
    
    def _scan_yaml_specific(self, file_path: str, content: str) -> List[SecurityIssue]:
        """Scans spécifiques aux fichiers YAML."""
        
        issues = []
        
        # Détection de secrets dans YAML
        if re.search(r'(?i)(password|secret|key|token):\s*[^\s]+', content):
            issues.append(SecurityIssue(
                severity="high",
                category="yaml_secrets",
                file_path=file_path,
                line_number=1,
                code_snippet="[YAML contains potential secrets]",
                description="Secrets potentiels détectés dans fichier YAML",
                recommendation="Utiliser variables d'environnement",
                confidence=0.7
            ))
        
        return issues
    
    def _get_issue_description(self, category: str, matched_text: str) -> str:
        """Retourne description détaillée de l'issue."""
        
        descriptions = {
            "hardcoded_secrets": f"Secret hardcodé détecté: {matched_text[:50]}...",
            "sql_injection": "Potentielle injection SQL détectée",
            "path_traversal": "Vulnérabilité path traversal potentielle",
            "unsafe_deserialization": "Désérialisation non sécurisée détectée",
            "input_validation": "Validation d'entrée insuffisante",
            "sensitive_logging": "Logging d'informations sensibles",
            "error_handling": "Gestion d'erreur trop générique"
        }
        
        return descriptions.get(category, f"Issue de sécurité détectée: {category}")
    
    def _get_recommendation(self, category: str) -> str:
        """Retourne recommandation pour résoudre l'issue."""
        
        recommendations = {
            "hardcoded_secrets": "Utiliser variables d'environnement ou gestionnaire de secrets",
            "sql_injection": "Utiliser requêtes préparées ou ORM sécurisé",
            "path_traversal": "Valider et sanitiser les chemins de fichiers",
            "unsafe_deserialization": "Utiliser des formats sécurisés comme JSON",
            "input_validation": "Valider et sanitiser toutes les entrées utilisateur",
            "sensitive_logging": "Éviter de logger des informations sensibles",
            "error_handling": "Implémenter gestion d'erreur spécifique"
        }
        
        return recommendations.get(category, "Suivre les bonnes pratiques de sécurité")
    
    def _calculate_confidence(self, category: str, matched_text: str) -> float:
        """Calcule score de confiance pour la détection."""
        
        # Base confidence par catégorie
        base_confidence = {
            "hardcoded_secrets": 0.8,
            "sql_injection": 0.7,
            "unsafe_deserialization": 0.9,
            "path_traversal": 0.6,
            "input_validation": 0.5
        }
        
        confidence = base_confidence.get(category, 0.6)
        
        # Ajustements selon contexte
        if "test" in matched_text.lower():
            confidence *= 0.5  # Moins critique dans tests
        
        if any(word in matched_text.lower() for word in ["example", "demo", "placeholder"]):
            confidence *= 0.3  # Probablement pas réel
        
        return min(confidence, 1.0)
    
    def _generate_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """Génère recommandations générales basées sur issues trouvées."""
        
        recommendations = []
        
        # Analyser patterns d'issues
        high_critical = [i for i in issues if i.severity in ["high", "critical"]]
        
        if high_critical:
            recommendations.append("🚨 URGENT: Corriger immédiatement les vulnérabilités critiques et hautes")
        
        categories = set(issue.category for issue in issues)
        
        if "hardcoded_secrets" in categories:
            recommendations.append("🔐 Migrer tous les secrets vers variables d'environnement")
        
        if "sql_injection" in categories:
            recommendations.append("🛡️ Implémenter requêtes paramétrées pour toutes les interactions DB")
        
        if "input_validation" in categories:
            recommendations.append("✅ Renforcer validation d'entrées utilisateur")
        
        # Recommandations générales
        recommendations.extend([
            "📝 Configurer pipeline CI/CD avec scans sécurité automatiques",
            "🔍 Implémenter monitoring sécurité temps réel",
            "📚 Former équipe aux bonnes pratiques sécurité",
            "🔄 Planifier audits sécurité réguliers"
        ])
        
        return recommendations
    
    def _evaluate_compliance(self, issues: List[SecurityIssue]) -> Dict[str, bool]:
        """Évalue compliance aux standards sécurité."""
        
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        
        return {
            "no_critical_vulnerabilities": len(critical_issues) == 0,
            "minimal_high_vulnerabilities": len(high_issues) <= 2,
            "secrets_management": not any("hardcoded_secrets" in i.category for i in issues),
            "input_validation": not any("sql_injection" in i.category for i in issues),
            "secure_deserialization": not any("unsafe_deserialization" in i.category for i in issues),
            "error_handling": len([i for i in issues if "error_handling" in i.category]) <= 5
        }
    
    def export_report(self, report: SecurityReport, output_file: str) -> None:
        """Exporte rapport au format JSON."""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Security report exported to {output_file}")
    
    def generate_html_report(self, report: SecurityReport, output_file: str) -> None:
        """Génère rapport HTML lisible."""
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phoenix Letters - Security Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .critical {{ color: #dc3545; font-weight: bold; }}
                .high {{ color: #fd7e14; font-weight: bold; }}
                .medium {{ color: #ffc107; }}
                .low {{ color: #28a745; }}
                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 10px; }}
                .issue {{ margin: 20px 0; padding: 15px; border-left: 4px solid #ddd; }}
                pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🛡️ Phoenix Letters - Rapport de Sécurité</h1>
            
            <div class="summary">
                <h2>📊 Résumé</h2>
                <p><strong>Date scan:</strong> {report.scan_timestamp}</p>
                <p><strong>Fichiers scannés:</strong> {report.total_files_scanned}</p>
                <p><strong>Issues totales:</strong> {report.total_issues}</p>
                <ul>
                    <li class="critical">Critiques: {report.issues_by_severity['critical']}</li>
                    <li class="high">Hautes: {report.issues_by_severity['high']}</li>
                    <li class="medium">Moyennes: {report.issues_by_severity['medium']}</li>
                    <li class="low">Basses: {report.issues_by_severity['low']}</li>
                </ul>
            </div>
            
            <h2>🔍 Issues Détectées</h2>
        """
        
        for issue in sorted(report.issues, key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[x.severity], reverse=True):
            html_template += f"""
            <div class="issue">
                <h3 class="{issue.severity}">{issue.severity.upper()} - {issue.category}</h3>
                <p><strong>Fichier:</strong> {issue.file_path}:{issue.line_number}</p>
                <p><strong>Description:</strong> {issue.description}</p>
                <pre>{issue.code_snippet}</pre>
                <p><strong>Recommandation:</strong> {issue.recommendation}</p>
            </div>
            """
        
        html_template += """
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        self.logger.info(f"HTML report generated: {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    import argparse
    
    parser = argparse.ArgumentParser(description="Phoenix Letters Security Scanner")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--output", "-o", default="security_report.json", help="Output file")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    
    args = parser.parse_args()
    
    scanner = PhoenixSecurityScanner()
    report = scanner.scan_directory(args.directory)
    
    scanner.export_report(report, args.output)
    
    if args.html:
        html_file = args.output.replace('.json', '.html')
        scanner.generate_html_report(report, html_file)
    
    print(f"Security scan completed. {report.total_issues} issues found.")
    print(f"Critical: {report.issues_by_severity['critical']}, High: {report.issues_by_severity['high']}")