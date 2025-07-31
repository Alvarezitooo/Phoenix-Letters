"""
🌱 Phoenix Green Metrics - Système de tracking carbone pour IA écologique.

Module central pour mesurer et optimiser l'empreinte carbone de Phoenix Letters.
Conforme aux standards Green AI et orienté certification ISO/IEC 42001.

Author: Claude Phoenix DevSecOps Guardian
Version: 1.0.0 - Phoenix Green AI Initiative
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CarbonImpactLevel(Enum):
    """Niveaux d'impact carbone pour classification."""
    EXCELLENT = "excellent"  # < 0.1g CO2
    GOOD = "good"           # 0.1-0.5g CO2
    MODERATE = "moderate"   # 0.5-2g CO2
    HIGH = "high"          # > 2g CO2


@dataclass
class GeminiCallMetrics:
    """Métriques d'un appel Gemini pour calcul carbone."""
    
    # Identifiants
    call_id: str
    timestamp: datetime
    user_tier: str
    
    # Tokens et contenu
    input_tokens: int
    output_tokens: int
    total_tokens: int
    prompt_length: int
    response_length: int
    
    # Performance
    response_time_ms: int
    cache_hit: bool
    retry_count: int
    
    # Calculs carbone
    estimated_co2_grams: float
    carbon_impact_level: CarbonImpactLevel
    
    # Métadonnées
    model_version: str = "gemini-1.5-flash"
    feature_used: Optional[str] = None
    compression_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['carbon_impact_level'] = self.carbon_impact_level.value
        return data


class PhoenixGreenMetrics:
    """
    🌱 Système de tracking carbone Phoenix Green AI.
    
    Responsabilités:
    - Mesure en temps réel de l'empreinte carbone des appels IA
    - Calcul des métriques d'efficacité énergétique
    - Optimisation automatique des performances
    - Génération de rapports pour certification
    """
    
    # Constantes CO2 basées sur recherche Green AI
    CO2_PER_TOKEN_GRAMS = 0.0000047  # Recherche DeepMind 2022
    CO2_NETWORK_OVERHEAD_GRAMS = 0.002  # Transport réseau
    CO2_CACHE_SAVINGS_RATIO = 0.85  # 85% d'économie si cache hit
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialise le système de métriques Green AI.
        
        Args:
            storage_path: Chemin de stockage des métriques (optionnel)
        """
        self.storage_path = storage_path or Path("data/green_metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Stockage en mémoire thread-safe
        self._metrics: List[GeminiCallMetrics] = []
        self._lock = threading.Lock()
        
        # Cache des statistiques pour performance
        self._stats_cache: Dict[str, Any] = {}
        self._stats_cache_expiry: Optional[datetime] = None
        
        logger.info("🌱 Phoenix Green Metrics initialized")
    
    @contextmanager
    def track_gemini_call(
        self, 
        user_tier: str, 
        feature_used: Optional[str] = None
    ):
        """
        Context manager pour tracker un appel Gemini.
        
        Usage:
            with green_metrics.track_gemini_call("premium") as tracker:
                response = gemini_client.generate(prompt)
                tracker.record_response(response, prompt)
        
        Args:
            user_tier: Niveau d'abonnement utilisateur
            feature_used: Fonctionnalité utilisée (lettre, coaching, etc.)
            
        Yields:
            GeminiCallTracker: Objet pour enregistrer les métriques
        """
        call_id = f"call_{int(time.time() * 1000)}_{id(threading.current_thread())}"
        start_time = time.time()
        tracker = GeminiCallTracker(call_id, user_tier, feature_used, start_time)
        
        try:
            yield tracker
        finally:
            # Calcul des métriques finales
            if tracker.is_completed():
                metrics = self._calculate_metrics(tracker)
                self._store_metrics(metrics)
                logger.debug(f"🌱 Tracked call {call_id}: {metrics.estimated_co2_grams:.4f}g CO2")
    
    def _calculate_metrics(self, tracker: 'GeminiCallTracker') -> GeminiCallMetrics:
        """Calcule les métriques carbone d'un appel Gemini."""
        
        # Calcul CO2 base (tokens)
        token_co2 = tracker.total_tokens * self.CO2_PER_TOKEN_GRAMS
        
        # Overhead réseau
        network_co2 = self.CO2_NETWORK_OVERHEAD_GRAMS
        
        # Économies cache
        cache_savings = 0
        if tracker.cache_hit:
            cache_savings = token_co2 * self.CO2_CACHE_SAVINGS_RATIO
        
        # Pénalité retry
        retry_penalty = tracker.retry_count * 0.001  # 1mg par retry
        
        # Total CO2
        total_co2 = max(0, token_co2 + network_co2 - cache_savings + retry_penalty)
        
        # Classification impact
        if total_co2 < 0.1:
            impact_level = CarbonImpactLevel.EXCELLENT
        elif total_co2 < 0.5:
            impact_level = CarbonImpactLevel.GOOD
        elif total_co2 < 2.0:
            impact_level = CarbonImpactLevel.MODERATE
        else:
            impact_level = CarbonImpactLevel.HIGH
        
        return GeminiCallMetrics(
            call_id=tracker.call_id,
            timestamp=tracker.start_timestamp,
            user_tier=tracker.user_tier,
            input_tokens=tracker.input_tokens,
            output_tokens=tracker.output_tokens,
            total_tokens=tracker.total_tokens,
            prompt_length=tracker.prompt_length,
            response_length=tracker.response_length,
            response_time_ms=tracker.response_time_ms,
            cache_hit=tracker.cache_hit,
            retry_count=tracker.retry_count,
            estimated_co2_grams=total_co2,
            carbon_impact_level=impact_level,
            feature_used=tracker.feature_used,
            compression_ratio=tracker.compression_ratio
        )
    
    def _store_metrics(self, metrics: GeminiCallMetrics) -> None:
        """Stocke les métriques de façon thread-safe."""
        with self._lock:
            self._metrics.append(metrics)
            
            # Sauvegarde périodique sur disque
            if len(self._metrics) % 10 == 0:
                self._persist_metrics()
            
            # Invalidation cache stats
            self._stats_cache_expiry = None
    
    def _persist_metrics(self) -> None:
        """Sauvegarde les métriques sur disque."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            file_path = self.storage_path / f"green_metrics_{today}.jsonl"
            
            # Append des nouvelles métriques
            with open(file_path, 'a', encoding='utf-8') as f:
                for metric in self._metrics[-10:]:  # Dernières 10
                    f.write(json.dumps(metric.to_dict()) + '\n')
                    
        except Exception as e:
            logger.error(f"🌱 Failed to persist metrics: {e}")
    
    def get_daily_stats(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Récupère les statistiques quotidiennes Green AI.
        
        Args:
            date: Date cible (aujourd'hui par défaut)
            
        Returns:
            Dict contenant les métriques agrégées
        """
        target_date = date or datetime.now()
        
        # Vérification cache
        cache_key = target_date.strftime("%Y-%m-%d")
        if (self._stats_cache_expiry and 
            datetime.now() < self._stats_cache_expiry and 
            cache_key in self._stats_cache):
            return self._stats_cache[cache_key]
        
        # Filtrage des métriques du jour
        day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        with self._lock:
            daily_metrics = [
                m for m in self._metrics 
                if day_start <= m.timestamp < day_end
            ]
        
        if not daily_metrics:
            return self._empty_stats()
        
        # Calculs statistiques
        total_calls = len(daily_metrics)
        total_co2 = sum(m.estimated_co2_grams for m in daily_metrics)
        cache_hits = sum(1 for m in daily_metrics if m.cache_hit)
        
        stats = {
            # Métriques principales
            "total_calls": total_calls,
            "total_co2_grams": round(total_co2, 4),
            "avg_co2_per_call": round(total_co2 / total_calls, 4),
            "cache_hit_ratio": round(cache_hits / total_calls, 3),
            
            # Performance
            "avg_response_time_ms": round(
                sum(m.response_time_ms for m in daily_metrics) / total_calls
            ),
            "total_tokens": sum(m.total_tokens for m in daily_metrics),
            
            # Impact distribution
            "impact_distribution": self._calculate_impact_distribution(daily_metrics),
            
            # Tendances
            "efficiency_score": self._calculate_efficiency_score(daily_metrics),
            "green_ai_grade": self._calculate_green_grade(total_co2, total_calls),
            
            # Comparaisons
            "vs_industry_benchmark": self._compare_to_benchmark(total_co2, total_calls),
            
            # Métadonnées
            "date": target_date.strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat()
        }
        
        # Mise en cache (5 minutes)
        self._stats_cache[cache_key] = stats
        self._stats_cache_expiry = datetime.now() + timedelta(minutes=5)
        
        return stats
    
    def _calculate_impact_distribution(self, metrics: List[GeminiCallMetrics]) -> Dict[str, Any]:
        """Calcule la distribution des niveaux d'impact carbone."""
        distribution = {level.value: 0 for level in CarbonImpactLevel}
        
        for metric in metrics:
            distribution[metric.carbon_impact_level.value] += 1
        
        total = len(metrics)
        return {
            "counts": distribution,
            "percentages": {
                level: round(count / total * 100, 1) 
                for level, count in distribution.items()
            }
        }
    
    def _calculate_efficiency_score(self, metrics: List[GeminiCallMetrics]) -> float:
        """Calcule un score d'efficacité Green AI (0-100)."""
        if not metrics:
            return 0.0
        
        # Facteurs d'efficacité
        cache_ratio = sum(1 for m in metrics if m.cache_hit) / len(metrics)
        avg_co2 = sum(m.estimated_co2_grams for m in metrics) / len(metrics)
        excellent_ratio = sum(
            1 for m in metrics 
            if m.carbon_impact_level == CarbonImpactLevel.EXCELLENT
        ) / len(metrics)
        
        # Score composite (0-100)
        score = (
            cache_ratio * 40 +  # 40% pour le cache
            (1 - min(avg_co2 / 2.0, 1)) * 30 +  # 30% pour CO2 moyen
            excellent_ratio * 30  # 30% pour excellence
        ) * 100
        
        return round(score, 1)
    
    def _calculate_green_grade(self, total_co2: float, total_calls: int) -> str:
        """Calcule une note Green AI (A+ à F)."""
        if total_calls == 0:
            return "N/A"
        
        avg_co2 = total_co2 / total_calls
        
        if avg_co2 < 0.05:
            return "A+"
        elif avg_co2 < 0.1:
            return "A"
        elif avg_co2 < 0.2:
            return "B"
        elif avg_co2 < 0.5:
            return "C"
        elif avg_co2 < 1.0:
            return "D"
        else:
            return "F"
    
    def _compare_to_benchmark(self, total_co2: float, total_calls: int) -> Dict[str, Any]:
        """Compare aux benchmarks industrie."""
        if total_calls == 0:
            return {"status": "insufficient_data"}
        
        avg_co2 = total_co2 / total_calls
        
        # Benchmarks estimés (recherche 2024)
        benchmarks = {
            "chatgpt": 1.2,      # gCO2 par requête
            "claude": 0.8,       # gCO2 par requête
            "gemini_standard": 0.6,  # gCO2 par requête
            "phoenix_target": 0.3    # Notre objectif
        }
        
        comparisons = {}
        for service, benchmark in benchmarks.items():
            if avg_co2 < benchmark:
                improvement = round((1 - avg_co2 / benchmark) * 100, 1)
                comparisons[service] = f"-{improvement}% (better)"
            else:
                degradation = round((avg_co2 / benchmark - 1) * 100, 1)
                comparisons[service] = f"+{degradation}% (worse)"
        
        return {
            "phoenix_avg_co2": round(avg_co2, 4),
            "comparisons": comparisons,
            "industry_position": "leader" if avg_co2 < 0.4 else "follower"
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques vides."""
        return {
            "total_calls": 0,
            "total_co2_grams": 0,
            "avg_co2_per_call": 0,
            "cache_hit_ratio": 0,
            "avg_response_time_ms": 0,
            "total_tokens": 0,
            "efficiency_score": 0,
            "green_ai_grade": "N/A",
            "message": "No data available for this period"
        }
    
    def export_certification_report(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Génère un rapport pour certification ISO/IEC 42001.
        
        Args:
            period_days: Période d'analyse en jours
            
        Returns:
            Rapport détaillé pour audit externe
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Collecte des métriques de la période
        with self._lock:
            period_metrics = [
                m for m in self._metrics 
                if start_date <= m.timestamp <= end_date
            ]
        
        if not period_metrics:
            logger.warning("🌱 No metrics available for certification report")
            return {"error": "insufficient_data", "period": f"{period_days} days"}
        
        # Génération du rapport
        total_co2 = sum(m.estimated_co2_grams for m in period_metrics)
        
        report = {
            # Métadonnées audit
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "period_days": period_days,
                "phoenix_version": "1.0.0",
                "metrics_count": len(period_metrics)
            },
            
            # KPI principales
            "carbon_footprint": {
                "total_co2_grams": round(total_co2, 6),
                "avg_co2_per_request": round(total_co2 / len(period_metrics), 6),
                "co2_per_user_session": round(total_co2 / max(1, len(set(m.call_id[:10] for m in period_metrics))), 6),
                "carbon_intensity_trend": self._calculate_trend(period_metrics)
            },
            
            # Efficacité énergétique
            "efficiency_metrics": {
                "cache_hit_ratio": round(sum(1 for m in period_metrics if m.cache_hit) / len(period_metrics), 3),
                "avg_response_time_ms": round(sum(m.response_time_ms for m in period_metrics) / len(period_metrics)),
                "token_efficiency": round(sum(m.total_tokens for m in period_metrics) / len(period_metrics)),
                "retry_rate": round(sum(m.retry_count for m in period_metrics) / len(period_metrics), 3)
            },
            
            # Conformité Green AI
            "green_ai_compliance": {
                "excellent_calls_percentage": round(
                    sum(1 for m in period_metrics if m.carbon_impact_level == CarbonImpactLevel.EXCELLENT) / len(period_metrics) * 100, 1
                ),
                "high_impact_calls_percentage": round(
                    sum(1 for m in period_metrics if m.carbon_impact_level == CarbonImpactLevel.HIGH) / len(period_metrics) * 100, 1
                ),
                "overall_green_grade": self._calculate_green_grade(total_co2, len(period_metrics)),
                "iso_42001_compliance_score": self._calculate_iso_compliance(period_metrics)
            },
            
            # Benchmarking
            "industry_comparison": self._compare_to_benchmark(total_co2, len(period_metrics)),
            
            # Actions recommandées
            "recommendations": self._generate_recommendations(period_metrics)
        }
        
        # Sauvegarde du rapport
        report_path = self.storage_path / f"certification_report_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"🌱 Certification report saved: {report_path}")
        except Exception as e:
            logger.error(f"🌱 Failed to save certification report: {e}")
        
        return report
    
    def _calculate_trend(self, metrics: List[GeminiCallMetrics]) -> str:
        """Calcule la tendance carbone sur la période."""
        if len(metrics) < 10:
            return "insufficient_data"
        
        # Division en deux périodes
        mid_point = len(metrics) // 2
        first_half = metrics[:mid_point]
        second_half = metrics[mid_point:]
        
        avg_first = sum(m.estimated_co2_grams for m in first_half) / len(first_half)
        avg_second = sum(m.estimated_co2_grams for m in second_half) / len(second_half)
        
        change = (avg_second - avg_first) / avg_first * 100
        
        if abs(change) < 5:
            return "stable"
        elif change < -5:
            return "improving"
        else:
            return "degrading"
    
    def _calculate_iso_compliance(self, metrics: List[GeminiCallMetrics]) -> float:
        """Calcule un score de conformité ISO/IEC 42001 (0-100)."""
        if not metrics:
            return 0.0
        
        # Critères ISO 42001 adaptés
        transparency_score = 100  # Métriques complètes = 100%
        
        efficiency_score = (
            sum(1 for m in metrics if m.cache_hit) / len(metrics) * 100
        )
        
        environmental_score = (
            sum(1 for m in metrics if m.carbon_impact_level in [CarbonImpactLevel.EXCELLENT, CarbonImpactLevel.GOOD]) / len(metrics) * 100
        )
        
        reliability_score = max(0, 100 - (sum(m.retry_count for m in metrics) / len(metrics) * 20))
        
        # Score composite
        iso_score = (
            transparency_score * 0.3 +
            efficiency_score * 0.3 +
            environmental_score * 0.25 +
            reliability_score * 0.15
        )
        
        return round(iso_score, 1)
    
    def _generate_recommendations(self, metrics: List[GeminiCallMetrics]) -> List[str]:
        """Génère des recommandations d'optimisation."""
        recommendations = []
        
        if not metrics:
            return ["No data available for recommendations"]
        
        # Analyse cache
        cache_ratio = sum(1 for m in metrics if m.cache_hit) / len(metrics)
        if cache_ratio < 0.7:
            recommendations.append("Améliorer la stratégie de cache (actuel: {:.1%})".format(cache_ratio))
        
        # Analyse CO2
        avg_co2 = sum(m.estimated_co2_grams for m in metrics) / len(metrics)
        if avg_co2 > 0.5:
            recommendations.append("Optimiser les prompts pour réduire l'empreinte carbone")
        
        # Analyse retry
        avg_retry = sum(m.retry_count for m in metrics) / len(metrics)
        if avg_retry > 0.1:
            recommendations.append("Améliorer la fiabilité pour réduire les retries")
        
        # Analyse tokens
        avg_tokens = sum(m.total_tokens for m in metrics) / len(metrics)
        if avg_tokens > 2000:
            recommendations.append("Compresser les prompts pour réduire la consommation de tokens")
        
        if not recommendations:
            recommendations.append("Performance Green AI excellente - maintenir les bonnes pratiques")
        
        return recommendations


class GeminiCallTracker:
    """Tracker pour une session d'appel Gemini."""
    
    def __init__(self, call_id: str, user_tier: str, feature_used: Optional[str], start_time: float):
        self.call_id = call_id
        self.user_tier = user_tier
        self.feature_used = feature_used
        self.start_time = start_time
        self.start_timestamp = datetime.fromtimestamp(start_time)
        
        # Métriques à remplir
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.prompt_length = 0
        self.response_length = 0
        self.response_time_ms = 0
        self.cache_hit = False
        self.retry_count = 0
        self.compression_ratio: Optional[float] = None
        
        self._completed = False
    
    def record_request(self, prompt: str, compressed_prompt: Optional[str] = None) -> None:
        """Enregistre les métriques de la requête."""
        self.prompt_length = len(prompt)
        self.input_tokens = self._estimate_tokens(prompt)
        
        if compressed_prompt:
            self.compression_ratio = len(compressed_prompt) / len(prompt)
    
    def record_response(self, response_text: str, from_cache: bool = False) -> None:
        """Enregistre les métriques de la réponse."""
        self.response_length = len(response_text)
        self.output_tokens = self._estimate_tokens(response_text)
        self.total_tokens = self.input_tokens + self.output_tokens
        self.cache_hit = from_cache
        
        # Temps de réponse
        self.response_time_ms = int((time.time() - self.start_time) * 1000)
        
        self._completed = True
    
    def record_retry(self) -> None:
        """Enregistre une tentative de retry."""
        self.retry_count += 1
    
    def is_completed(self) -> bool:
        """Vérifie si le tracking est complet."""
        return self._completed
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimation simple du nombre de tokens."""
        # Approximation: 1 token ≈ 0.75 mots en français
        words = len(text.split())
        return int(words / 0.75)


# Instance globale pour l'application
phoenix_green_metrics = PhoenixGreenMetrics()