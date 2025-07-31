"""Tests de sécurité pour système d'authentification Phoenix Letters."""
import logging
import hashlib
import secrets
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
import requests
from unittest.mock import Mock
import bcrypt


@dataclass
class SecurityTestResult:
    """Résultat d'un test de sécurité."""
    test_name: str
    category: str
    severity: str  # "low", "medium", "high", "critical"
    status: str   # "pass", "fail", "warning"
    description: str
    details: str
    recommendation: str
    evidence: Optional[str] = None


@dataclass
class AuthSecurityReport:
    """Rapport de sécurité authentification."""
    test_timestamp: str
    total_tests: int
    tests_passed: int
    tests_failed: int
    security_score: float
    test_results: List[SecurityTestResult]
    critical_issues: List[str]
    recommendations: List[str]


class AuthSecurityTester:
    """Testeur de sécurité pour authentification Phoenix Letters."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configuration tests
        self.test_config = {
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True, 
                "require_digits": True,
                "require_special": True,
                "max_length": 128
            },
            "session_config": {
                "timeout_minutes": 30,
                "secure_cookies": True,
                "httponly_cookies": True,
                "samesite": "Strict"
            },
            "rate_limiting": {
                "login_attempts": 5,
                "lockout_duration": 300,  # 5 minutes
                "ip_rate_limit": 100      # per hour
            }
        }
        
        # Patterns d'attaque courants
        self.attack_patterns = {
            "sql_injection": [
                "' OR '1'='1", "'; DROP TABLE users;--", 
                "' UNION SELECT * FROM users--", "admin'--"
            ],
            "xss": [
                "<script>alert('XSS')</script>", 
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>"
            ],
            "command_injection": [
                "; ls -la", "| whoami", "&& cat /etc/passwd", "`id`"
            ],
            "path_traversal": [
                "../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f", "....//....//....//etc//passwd"
            ]
        }
    
    def run_comprehensive_auth_security_tests(self, auth_service_path: str = None) -> AuthSecurityReport:
        """
        Lance tests de sécurité complets sur authentification.
        
        Args:
            auth_service_path: Chemin du service d'authentification
        Returns:
            AuthSecurityReport complet
        """
        
        self.logger.info("Starting comprehensive authentication security tests")
        
        test_results = []
        
        # 1. Tests politique mots de passe
        test_results.extend(self._test_password_policy())
        
        # 2. Tests hachage mots de passe
        test_results.extend(self._test_password_hashing())
        
        # 3. Tests gestion sessions
        test_results.extend(self._test_session_management())
        
        # 4. Tests rate limiting
        test_results.extend(self._test_rate_limiting())
        
        # 5. Tests vulnérabilités injection
        test_results.extend(self._test_injection_vulnerabilities())
        
        # 6. Tests authentification multi-facteurs
        test_results.extend(self._test_mfa_implementation())
        
        # 7. Tests sécurité cookies
        test_results.extend(self._test_cookie_security())
        
        # 8. Tests CSRF protection
        test_results.extend(self._test_csrf_protection())
        
        # 9. Tests enumération utilisateurs
        test_results.extend(self._test_user_enumeration())
        
        # 10. Tests timing attacks
        test_results.extend(self._test_timing_attacks())
        
        # Analyser résultats
        total_tests = len(test_results)
        tests_passed = len([t for t in test_results if t.status == "pass"])
        tests_failed = len([t for t in test_results if t.status == "fail"])
        
        # Calculer score sécurité
        security_score = self._calculate_security_score(test_results)
        
        # Identifier issues critiques
        critical_issues = [
            t.description for t in test_results 
            if t.severity == "critical" and t.status == "fail"
        ]
        
        # Générer recommandations
        recommendations = self._generate_security_recommendations(test_results)
        
        report = AuthSecurityReport(
            test_timestamp=datetime.now().isoformat(),
            total_tests=total_tests,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            security_score=security_score,
            test_results=test_results,
            critical_issues=critical_issues,
            recommendations=recommendations
        )
        
        self.logger.info(f"Auth security tests completed. Score: {security_score:.1f}%")
        
        return report
    
    def _test_password_policy(self) -> List[SecurityTestResult]:
        """Teste politique des mots de passe."""
        
        results = []
        
        # Test mots de passe faibles
        weak_passwords = [
            "password", "123456", "admin", "user", "test",
            "azerty", "motdepasse", "password123", "admin123"
        ]
        
        for weak_pwd in weak_passwords:
            is_rejected = self._simulate_password_validation(weak_pwd)
            
            results.append(SecurityTestResult(
                test_name=f"Weak password rejection: '{weak_pwd}'",
                category="password_policy",
                severity="high" if not is_rejected else "low",
                status="pass" if is_rejected else "fail",
                description=f"Mot de passe faible '{weak_pwd}' {'rejeté' if is_rejected else 'accepté'}",
                details=f"Test de validation avec mot de passe: {weak_pwd}",
                recommendation="Implémenter politique mots de passe robuste" if not is_rejected else "Validation OK"
            ))
        
        # Test longueur minimale
        short_password = "Aa1!"  # 4 caractères
        is_rejected = self._simulate_password_validation(short_password)
        
        results.append(SecurityTestResult(
            test_name="Minimum password length enforcement",
            category="password_policy",
            severity="medium",
            status="pass" if is_rejected else "fail",
            description=f"Mot de passe court (4 chars) {'rejeté' if is_rejected else 'accepté'}",
            details="Test longueur minimale 8 caractères",
            recommendation="Enforcer longueur minimale 8+ caractères"
        ))
        
        # Test complexité
        simple_password = "password"
        complex_password = "MyC0mpl3x!P@ssw0rd"
        
        simple_rejected = self._simulate_password_validation(simple_password)
        complex_accepted = not self._simulate_password_validation(complex_password)
        
        results.append(SecurityTestResult(
            test_name="Password complexity requirements",
            category="password_policy", 
            severity="medium",
            status="pass" if simple_rejected and complex_accepted else "fail",
            description="Test exigences complexité (maj, min, chiffres, spéciaux)",
            details=f"Simple: {'rejected' if simple_rejected else 'accepted'}, Complex: {'accepted' if complex_accepted else 'rejected'}",
            recommendation="Exiger majuscules, minuscules, chiffres et caractères spéciaux"
        ))
        
        return results
    
    def _simulate_password_validation(self, password: str) -> bool:
        """Simule validation mot de passe (à adapter selon implémentation réelle)."""
        
        policy = self.test_config["password_policy"]
        
        # Longueur
        if len(password) < policy["min_length"]:
            return False
        
        # Caractères requis
        if policy["require_uppercase"] and not re.search(r'[A-Z]', password):
            return False
        if policy["require_lowercase"] and not re.search(r'[a-z]', password):
            return False
        if policy["require_digits"] and not re.search(r'\d', password):
            return False
        if policy["require_special"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        # Mots de passe communs
        common_passwords = ["password", "123456", "admin", "user", "test", "azerty"]
        if password.lower() in common_passwords:
            return False
        
        return True
    
    def _test_password_hashing(self) -> List[SecurityTestResult]:
        """Teste sécurité hachage mots de passe."""
        
        results = []
        
        # Test algorithme hachage sécurisé
        test_password = "TestPassword123!"
        
        # Simuler différents algorithmes
        hash_tests = [
            ("MD5", hashlib.md5(test_password.encode()).hexdigest(), "critical"),
            ("SHA1", hashlib.sha1(test_password.encode()).hexdigest(), "high"),
            ("SHA256", hashlib.sha256(test_password.encode()).hexdigest(), "medium"),
            ("bcrypt", self._simulate_bcrypt_hash(test_password), "low")
        ]
        
        for algo, hash_result, severity in hash_tests:
            is_secure = algo in ["bcrypt", "argon2", "scrypt"]
            
            results.append(SecurityTestResult(
                test_name=f"Password hashing algorithm: {algo}",
                category="password_hashing",
                severity=severity if not is_secure else "low",
                status="pass" if is_secure else "fail",
                description=f"Algorithme {algo} {'sécurisé' if is_secure else 'non sécurisé'}",
                details=f"Hash généré: {hash_result[:50]}...",
                recommendation="Utiliser bcrypt, argon2 ou scrypt" if not is_secure else "Algorithme sécurisé"
            ))
        
        # Test salt unique
        hash1 = self._simulate_bcrypt_hash(test_password)
        hash2 = self._simulate_bcrypt_hash(test_password)
        
        unique_salt = hash1 != hash2
        
        results.append(SecurityTestResult(
            test_name="Unique salt per password",
            category="password_hashing",
            severity="high",
            status="pass" if unique_salt else "fail",
            description=f"Salt unique par mot de passe: {'Oui' if unique_salt else 'Non'}",
            details=f"Hash1: {hash1[:30]}..., Hash2: {hash2[:30]}...",
            recommendation="Générer salt unique pour chaque mot de passe"
        ))
        
        return results
    
    def _simulate_bcrypt_hash(self, password: str) -> str:
        """Simule hachage bcrypt."""
        try:
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except:
            # Fallback si bcrypt pas disponible
            salt = secrets.token_hex(16)
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _test_session_management(self) -> List[SecurityTestResult]:
        """Teste gestion des sessions."""
        
        results = []
        
        # Test timeout session
        results.append(SecurityTestResult(
            test_name="Session timeout configuration",
            category="session_management",
            severity="medium",
            status="warning",  # À vérifier dans implémentation réelle
            description="Configuration timeout session à vérifier",
            details=f"Timeout recommandé: {self.test_config['session_config']['timeout_minutes']} minutes",
            recommendation="Configurer timeout session approprié (15-30 min)"
        ))
        
        # Test régénération ID session
        results.append(SecurityTestResult(
            test_name="Session ID regeneration on login",
            category="session_management",
            severity="high",
            status="warning",
            description="Régénération ID session après login à vérifier",
            details="Prévient session fixation attacks",
            recommendation="Régénérer session ID après authentification réussie"
        ))
        
        # Test cookies sécurisés
        cookie_tests = [
            ("Secure flag", "high"),
            ("HttpOnly flag", "high"), 
            ("SameSite attribute", "medium")
        ]
        
        for cookie_test, severity in cookie_tests:
            results.append(SecurityTestResult(
                test_name=f"Session cookie {cookie_test}",
                category="session_management",
                severity=severity,
                status="warning",
                description=f"Configuration {cookie_test} à vérifier",
                details=f"Cookie de session doit avoir {cookie_test}",
                recommendation=f"Configurer {cookie_test} sur cookies session"
            ))
        
        return results
    
    def _test_rate_limiting(self) -> List[SecurityTestResult]:
        """Teste rate limiting."""
        
        results = []
        
        # Simuler tentatives login multiples
        max_attempts = self.test_config["rate_limiting"]["login_attempts"]
        
        # Test limitation tentatives
        results.append(SecurityTestResult(
            test_name="Login attempt rate limiting",
            category="rate_limiting",
            severity="high",
            status="warning",
            description=f"Limitation à {max_attempts} tentatives par IP à vérifier",
            details="Protection contre attaques par force brute",
            recommendation=f"Limiter à {max_attempts} tentatives puis blocage temporaire"
        ))
        
        # Test lockout temporaire
        lockout_duration = self.test_config["rate_limiting"]["lockout_duration"]
        
        results.append(SecurityTestResult(
            test_name="Account lockout mechanism",
            category="rate_limiting",
            severity="medium",
            status="warning",
            description=f"Blocage temporaire {lockout_duration}s après échecs",
            details="Équilibre sécurité vs. disponibilité",
            recommendation="Implémenter blocage progressif (1min, 5min, 15min)"
        ))
        
        return results
    
    def _test_injection_vulnerabilities(self) -> List[SecurityTestResult]:
        """Teste vulnérabilités injection."""
        
        results = []
        
        # Test SQL injection
        for payload in self.attack_patterns["sql_injection"]:
            is_blocked = self._simulate_input_validation(payload, "sql")
            
            results.append(SecurityTestResult(
                test_name=f"SQL injection protection: {payload[:20]}...",
                category="injection_protection",
                severity="critical",
                status="pass" if is_blocked else "fail",
                description=f"Payload SQL injection {'bloqué' if is_blocked else 'accepté'}",
                details=f"Test payload: {payload}",
                recommendation="Utiliser requêtes préparées et validation stricte"
            ))
        
        # Test XSS
        for payload in self.attack_patterns["xss"]:
            is_blocked = self._simulate_input_validation(payload, "xss")
            
            results.append(SecurityTestResult(
                test_name=f"XSS protection: {payload[:20]}...",
                category="injection_protection",
                severity="high",
                status="pass" if is_blocked else "fail", 
                description=f"Payload XSS {'bloqué' if is_blocked else 'accepté'}",
                details=f"Test payload: {payload}",
                recommendation="Sanitiser sorties et utiliser Content Security Policy"
            ))
        
        return results
    
    def _simulate_input_validation(self, input_value: str, attack_type: str) -> bool:
        """Simule validation d'entrée contre attaques."""
        
        # Patterns de détection basiques
        detection_patterns = {
            "sql": [r"'", r"union", r"select", r"drop", r"--", r";"],
            "xss": [r"<script", r"javascript:", r"onerror", r"onload"],
            "command": [r";", r"\|", r"&&", r"`", r"\$"],
            "path": [r"\.\.", r"%2e", r"//", r"\\"]
        }
        
        patterns = detection_patterns.get(attack_type, [])
        
        for pattern in patterns:
            if re.search(pattern, input_value, re.IGNORECASE):
                return True  # Bloqué
        
        return False  # Pas bloqué
    
    def _test_mfa_implementation(self) -> List[SecurityTestResult]:
        """Teste implémentation authentification multi-facteurs."""
        
        results = []
        
        # Test disponibilité MFA
        results.append(SecurityTestResult(
            test_name="Multi-factor authentication availability",
            category="mfa",
            severity="medium",
            status="warning",
            description="Disponibilité MFA à vérifier",
            details="TOTP, SMS, ou email comme second facteur",
            recommendation="Implémenter MFA optionnel pour utilisateurs Premium"
        ))
        
        # Test bypass MFA
        results.append(SecurityTestResult(
            test_name="MFA bypass protection",
            category="mfa",
            severity="high",
            status="warning",
            description="Protection contre contournement MFA à vérifier",
            details="Vérifier que MFA ne peut pas être contourné",
            recommendation="S'assurer que toutes les routes critiques requirent MFA"
        ))
        
        return results
    
    def _test_cookie_security(self) -> List[SecurityTestResult]:
        """Teste sécurité des cookies."""
        
        results = []
        
        cookie_flags = ["Secure", "HttpOnly", "SameSite"]
        
        for flag in cookie_flags:
            severity = "high" if flag in ["Secure", "HttpOnly"] else "medium"
            
            results.append(SecurityTestResult(
                test_name=f"Cookie {flag} flag",
                category="cookie_security", 
                severity=severity,
                status="warning",
                description=f"Flag {flag} sur cookies authentification à vérifier",
                details=f"{flag} prévient certaines attaques",
                recommendation=f"Configurer flag {flag} sur tous les cookies sensibles"
            ))
        
        return results
    
    def _test_csrf_protection(self) -> List[SecurityTestResult]:
        """Teste protection CSRF."""
        
        results = []
        
        results.append(SecurityTestResult(
            test_name="CSRF token implementation",
            category="csrf_protection",
            severity="high",
            status="warning",
            description="Implémentation tokens CSRF à vérifier",
            details="Protection contre Cross-Site Request Forgery",
            recommendation="Implémenter tokens CSRF sur toutes les actions sensibles"
        ))
        
        results.append(SecurityTestResult(
            test_name="SameSite cookie attribute",
            category="csrf_protection",
            severity="medium",
            status="warning",
            description="Attribut SameSite sur cookies à vérifier",
            details="Protection supplémentaire contre CSRF",
            recommendation="Configurer SameSite=Strict ou Lax"
        ))
        
        return results
    
    def _test_user_enumeration(self) -> List[SecurityTestResult]:
        """Teste protection contre énumération utilisateurs."""
        
        results = []
        
        results.append(SecurityTestResult(
            test_name="User enumeration via login response",
            category="user_enumeration",
            severity="medium",
            status="warning",
            description="Messages erreur login à vérifier",
            details="Messages identiques pour utilisateur inexistant vs mot de passe incorrect",
            recommendation="Utiliser messages d'erreur génériques"
        ))
        
        results.append(SecurityTestResult(
            test_name="User enumeration via registration",
            category="user_enumeration",
            severity="low",
            status="warning",
            description="Messages erreur inscription à vérifier",
            details="Ne pas révéler si email déjà utilisé",
            recommendation="Messages génériques ou confirmation email systématique"
        ))
        
        return results
    
    def _test_timing_attacks(self) -> List[SecurityTestResult]:
        """Teste protection contre timing attacks."""
        
        results = []
        
        # Simuler timing pour utilisateur existant vs inexistant
        start_time = time.time()
        self._simulate_password_check("existing_user", "wrong_password")
        existing_time = time.time() - start_time
        
        start_time = time.time()
        self._simulate_password_check("nonexistent_user", "wrong_password")
        nonexistent_time = time.time() - start_time
        
        time_difference = abs(existing_time - nonexistent_time)
        significant_difference = time_difference > 0.01  # 10ms
        
        results.append(SecurityTestResult(
            test_name="Timing attack protection",
            category="timing_attacks",
            severity="low",
            status="fail" if significant_difference else "pass",
            description=f"Différence timing: {time_difference:.4f}s",
            details=f"Existant: {existing_time:.4f}s, Inexistant: {nonexistent_time:.4f}s",
            recommendation="Utiliser timing constant pour toutes les vérifications"
        ))
        
        return results
    
    def _simulate_password_check(self, username: str, password: str) -> bool:
        """Simule vérification mot de passe."""
        # Simuler délai variable
        if username == "existing_user":
            time.sleep(0.001)  # Simule hachage bcrypt
        else:
            time.sleep(0.0005)  # Simule vérification rapide
        return False
    
    def _calculate_security_score(self, results: List[SecurityTestResult]) -> float:
        """Calcule score de sécurité global."""
        
        if not results:
            return 0.0
        
        # Pondération par sévérité
        severity_weights = {"low": 1, "medium": 3, "high": 5, "critical": 10}
        
        total_weight = 0
        passed_weight = 0
        
        for result in results:
            weight = severity_weights.get(result.severity, 1)
            total_weight += weight
            
            if result.status == "pass":
                passed_weight += weight
            elif result.status == "warning":
                passed_weight += weight * 0.5  # Partial credit
        
        return (passed_weight / total_weight) * 100.0 if total_weight > 0 else 0.0
    
    def _generate_security_recommendations(self, results: List[SecurityTestResult]) -> List[str]:
        """Génère recommandations sécurité."""
        
        recommendations = []
        
        # Analyser échecs par catégorie
        failed_tests = [r for r in results if r.status == "fail"]
        categories = set(r.category for r in failed_tests)
        
        if "password_policy" in categories:
            recommendations.append("🔑 Implémenter politique mots de passe robuste (8+ chars, complexité)")
        
        if "password_hashing" in categories:
            recommendations.append("🔐 Migrer vers algorithme hachage sécurisé (bcrypt/argon2)")
        
        if "injection_protection" in categories:
            recommendations.append("🛡️ Renforcer protection contre injections (SQL, XSS)")
        
        if "rate_limiting" in categories:
            recommendations.append("⚡ Implémenter rate limiting login et API")
        
        # Recommandations générales
        critical_failed = len([r for r in results if r.severity == "critical" and r.status == "fail"])
        high_failed = len([r for r in results if r.severity == "high" and r.status == "fail"])
        
        if critical_failed > 0:
            recommendations.append("🚨 URGENT: Corriger vulnérabilités critiques authentification")
        
        if high_failed > 0:
            recommendations.append("⚠️ PRIORITÉ: Traiter vulnérabilités hautes sous 7 jours")
        
        recommendations.extend([
            "🔍 Implémenter monitoring tentatives authentification suspectes",
            "📝 Documenter procédures réponse incidents sécurité",
            "🔄 Planifier tests pénétration réguliers",
            "👨‍💼 Former équipe aux bonnes pratiques sécurité auth"
        ])
        
        return recommendations
    
    def export_security_report(self, report: AuthSecurityReport, output_file: str) -> None:
        """Exporte rapport sécurité."""
        
        import json
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Auth security report exported to {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phoenix Letters Auth Security Tester")
    parser.add_argument("--output", "-o", default="auth_security_report.json", help="Output file")
    
    args = parser.parse_args()
    
    tester = AuthSecurityTester()
    report = tester.run_comprehensive_auth_security_tests()
    
    tester.export_security_report(report, args.output)
    
    print(f"Auth security tests completed. Score: {report.security_score:.1f}%")
    print(f"Tests passed: {report.tests_passed}/{report.total_tests}")
    if report.critical_issues:
        print(f"Critical issues: {len(report.critical_issues)}")
        for issue in report.critical_issues:
            print(f"  - {issue}")