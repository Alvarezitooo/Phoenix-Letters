"""
Tests unitaires pour le système Phoenix Green Metrics.

Tests complets du tracking carbone et des métriques Green AI,
incluant les cas d'usage certification ISO/IEC 42001.

Author: Claude Phoenix DevSecOps Guardian
Version: 1.0.0 - Phoenix Green AI Initiative
"""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from infrastructure.monitoring.phoenix_green_metrics import (
    PhoenixGreenMetrics,
    CarbonImpactLevel,
    GeminiCallMetrics,
    GeminiCallTracker
)


class TestPhoenixGreenMetrics:
    """Tests du système de métriques Green AI."""
    
    @pytest.fixture
    def temp_storage(self):
        """Répertoire temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def green_metrics(self, temp_storage):
        """Instance de PhoenixGreenMetrics pour tests."""
        return PhoenixGreenMetrics(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_metrics(self):
        """Métriques d'exemple pour tests."""
        return GeminiCallMetrics(
            call_id="test_call_001",
            timestamp=datetime.now(),
            user_tier="premium",
            input_tokens=150,
            output_tokens=300,
            total_tokens=450,
            prompt_length=600,
            response_length=1200,
            response_time_ms=1500,
            cache_hit=True,
            retry_count=0,
            estimated_co2_grams=0.08,
            carbon_impact_level=CarbonImpactLevel.EXCELLENT,
            feature_used="letter_generation"
        )
    
    def test_initialization(self, temp_storage):
        """Test d'initialisation du système."""
        metrics = PhoenixGreenMetrics(storage_path=temp_storage)
        
        assert metrics.storage_path == temp_storage
        assert temp_storage.exists()
        assert len(metrics._metrics) == 0
        assert metrics._stats_cache == {}
    
    def test_carbon_calculation_excellent(self, green_metrics):
        """Test calcul CO2 niveau excellent."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000)
        tracker.record_request("Test prompt for letter generation")
        tracker.record_response("Generated response text", from_cache=True)
        
        metrics = green_metrics._calculate_metrics(tracker)
        
        # Vérifications CO2
        assert metrics.estimated_co2_grams < 0.1
        assert metrics.carbon_impact_level == CarbonImpactLevel.EXCELLENT
        assert metrics.cache_hit is True
    
    def test_carbon_calculation_high_impact(self, green_metrics):
        """Test calcul CO2 impact élevé."""
        tracker = GeminiCallTracker("test_002", "free", "coaching", 1000)
        
        # Prompt très long pour augmenter les tokens
        long_prompt = "Very long prompt " * 500
        tracker.record_request(long_prompt)
        
        # Réponse longue, pas de cache, avec retries
        long_response = "Very long response " * 300
        tracker.record_response(long_response, from_cache=False)
        tracker.record_retry()
        tracker.record_retry()
        
        metrics = green_metrics._calculate_metrics(tracker)
        
        # Vérifications impact élevé
        assert metrics.estimated_co2_grams > 2.0
        assert metrics.carbon_impact_level == CarbonImpactLevel.HIGH
        assert metrics.cache_hit is False
        assert metrics.retry_count == 2
    
    def test_tracking_context_manager(self, green_metrics):
        """Test du context manager de tracking."""
        with green_metrics.track_gemini_call("premium", "letter") as tracker:
            assert tracker.user_tier == "premium"
            assert tracker.feature_used == "letter"
            
            tracker.record_request("Test prompt")
            tracker.record_response("Test response")
        
        # Vérification stockage
        assert len(green_metrics._metrics) == 1
        stored_metric = green_metrics._metrics[0]
        assert stored_metric.user_tier == "premium"
        assert stored_metric.feature_used == "letter"
    
    def test_daily_stats_empty(self, green_metrics):
        """Test statistiques journalières sans données."""
        stats = green_metrics.get_daily_stats()
        
        assert stats["total_calls"] == 0
        assert stats["total_co2_grams"] == 0
        assert stats["avg_co2_per_call"] == 0
        assert stats["cache_hit_ratio"] == 0
        assert stats["green_ai_grade"] == "N/A"
    
    def test_daily_stats_with_data(self, green_metrics, sample_metrics):
        """Test statistiques avec données."""
        # Injection de métriques test
        green_metrics._metrics = [sample_metrics]
        
        stats = green_metrics.get_daily_stats()
        
        assert stats["total_calls"] == 1
        assert stats["total_co2_grams"] == 0.08
        assert stats["avg_co2_per_call"] == 0.08
        assert stats["cache_hit_ratio"] == 1.0
        assert stats["green_ai_grade"] == "A+"
        assert stats["efficiency_score"] > 90
    
    def test_impact_distribution(self, green_metrics):
        """Test calcul distribution impact carbone."""
        # Création de métriques variées
        metrics_list = [
            self._create_metric_with_impact(CarbonImpactLevel.EXCELLENT),
            self._create_metric_with_impact(CarbonImpactLevel.EXCELLENT),
            self._create_metric_with_impact(CarbonImpactLevel.GOOD),
            self._create_metric_with_impact(CarbonImpactLevel.HIGH)
        ]
        
        distribution = green_metrics._calculate_impact_distribution(metrics_list)
        
        assert distribution["counts"]["excellent"] == 2
        assert distribution["counts"]["good"] == 1
        assert distribution["counts"]["high"] == 1
        assert distribution["percentages"]["excellent"] == 50.0
        assert distribution["percentages"]["good"] == 25.0
    
    def test_efficiency_score_calculation(self, green_metrics):
        """Test calcul du score d'efficacité."""
        # Métriques avec bon cache ratio et faible CO2
        metrics_list = [
            self._create_metric_with_cache(True, 0.05),
            self._create_metric_with_cache(True, 0.06),
            self._create_metric_with_cache(False, 0.15),
            self._create_metric_with_cache(True, 0.04)
        ]
        
        score = green_metrics._calculate_efficiency_score(metrics_list)
        
        # Score élevé attendu (bon cache + faible CO2)
        assert score > 80
        assert score <= 100
    
    def test_green_grade_calculation(self, green_metrics):
        """Test calcul de la note Green AI."""
        # Test différents niveaux
        assert green_metrics._calculate_green_grade(0.04, 1) == "A+"
        assert green_metrics._calculate_green_grade(0.08, 1) == "A"
        assert green_metrics._calculate_green_grade(0.15, 1) == "B"
        assert green_metrics._calculate_green_grade(0.3, 1) == "C"
        assert green_metrics._calculate_green_grade(0.8, 1) == "D"
        assert green_metrics._calculate_green_grade(1.5, 1) == "F"
        assert green_metrics._calculate_green_grade(0.0, 0) == "N/A"
    
    def test_benchmark_comparison(self, green_metrics):
        """Test comparaison avec benchmarks industrie."""
        comparison = green_metrics._compare_to_benchmark(0.3, 10)  # 0.03g CO2 moyen
        
        assert comparison["phoenix_avg_co2"] == 0.03
        assert comparison["industry_position"] == "leader"
        assert "better" in comparison["comparisons"]["chatgpt"]
        assert "better" in comparison["comparisons"]["gemini_standard"]
    
    def test_certification_report_generation(self, green_metrics):
        """Test génération rapport certification."""
        # Ajout de métriques de test
        test_metrics = [
            self._create_metric_with_impact(CarbonImpactLevel.EXCELLENT),
            self._create_metric_with_impact(CarbonImpactLevel.GOOD),
            self._create_metric_with_impact(CarbonImpactLevel.MODERATE)
        ]
        green_metrics._metrics = test_metrics
        
        report = green_metrics.export_certification_report(period_days=7)
        
        # Vérifications structure rapport
        assert "report_metadata" in report
        assert "carbon_footprint" in report
        assert "efficiency_metrics" in report
        assert "green_ai_compliance" in report
        assert "industry_comparison" in report
        assert "recommendations" in report
        
        # Vérifications contenu
        assert report["report_metadata"]["metrics_count"] == 3
        assert "iso_42001_compliance_score" in report["green_ai_compliance"]
        assert isinstance(report["recommendations"], list)
    
    def test_persistence_metrics(self, green_metrics, temp_storage):
        """Test persistance des métriques sur disque."""
        # Ajout de métriques pour déclencher la sauvegarde
        for i in range(10):
            metric = self._create_metric_with_impact(CarbonImpactLevel.GOOD)
            metric.call_id = f"test_call_{i:03d}"
            green_metrics._metrics.append(metric)
        
        # Déclenchement de la persistance
        green_metrics._persist_metrics()
        
        # Vérification fichier créé
        today = datetime.now().strftime("%Y-%m-%d")
        expected_file = temp_storage / f"green_metrics_{today}.jsonl"
        
        assert expected_file.exists()
        
        # Vérification contenu
        with open(expected_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 10
            
            # Vérification JSON valide
            first_metric = json.loads(lines[0])
            assert "call_id" in first_metric
            assert "estimated_co2_grams" in first_metric
    
    def test_trend_calculation(self, green_metrics):
        """Test calcul des tendances."""
        # Tendance dégradante (CO2 augmente)
        degrading_metrics = []
        for i in range(20):
            co2 = 0.05 + (i * 0.02)  # CO2 croissant
            metric = self._create_metric_with_co2(co2)
            degrading_metrics.append(metric)
        
        trend = green_metrics._calculate_trend(degrading_metrics)
        assert trend == "degrading"
        
        # Tendance améliorante (CO2 diminue)
        improving_metrics = []
        for i in range(20):
            co2 = 0.2 - (i * 0.005)  # CO2 décroissant
            metric = self._create_metric_with_co2(co2)
            improving_metrics.append(metric)
        
        trend = green_metrics._calculate_trend(improving_metrics)
        assert trend == "improving"
    
    def test_iso_compliance_score(self, green_metrics):
        """Test calcul score conformité ISO/IEC 42001."""
        # Métriques excellentes
        excellent_metrics = [
            self._create_metric_with_cache(True, 0.02),  # Cache + faible CO2
            self._create_metric_with_cache(True, 0.03),
            self._create_metric_with_cache(True, 0.04)
        ]
        
        score = green_metrics._calculate_iso_compliance(excellent_metrics)
        assert score > 90
        
        # Métriques moyennes
        average_metrics = [
            self._create_metric_with_cache(False, 0.5),  # Pas de cache + CO2 moyen
            self._create_metric_with_cache(True, 0.3),
            self._create_metric_with_cache(False, 0.8)
        ]
        
        score = green_metrics._calculate_iso_compliance(average_metrics)
        assert 50 < score < 90
    
    def test_recommendations_generation(self, green_metrics):
        """Test génération des recommandations."""
        # Métriques avec problèmes identifiables
        problematic_metrics = [
            self._create_metric_with_cache(False, 0.8),  # Cache faible
            self._create_metric_with_cache(False, 1.2),  # CO2 élevé
        ]
        
        # Ajout de retries
        problematic_metrics[0].retry_count = 2
        problematic_metrics[1].retry_count = 1
        
        recommendations = green_metrics._generate_recommendations(problematic_metrics)
        
        # Vérifications recommandations pertinentes
        assert len(recommendations) > 0
        cache_rec = any("cache" in rec.lower() for rec in recommendations)
        co2_rec = any("carbone" in rec.lower() or "co2" in rec.lower() for rec in recommendations)
        
        assert cache_rec or co2_rec  # Au moins une recommandation pertinente
    
    # Méthodes utilitaires pour les tests
    
    def _create_metric_with_impact(self, impact_level: CarbonImpactLevel) -> GeminiCallMetrics:
        """Crée une métrique avec un niveau d'impact spécifique."""
        co2_map = {
            CarbonImpactLevel.EXCELLENT: 0.05,
            CarbonImpactLevel.GOOD: 0.3,
            CarbonImpactLevel.MODERATE: 1.0,
            CarbonImpactLevel.HIGH: 3.0
        }
        
        return GeminiCallMetrics(
            call_id=f"test_{impact_level.value}",
            timestamp=datetime.now(),
            user_tier="premium",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            prompt_length=400,
            response_length=800,
            response_time_ms=1200,
            cache_hit=False,
            retry_count=0,
            estimated_co2_grams=co2_map[impact_level],
            carbon_impact_level=impact_level
        )
    
    def _create_metric_with_cache(self, cache_hit: bool, co2_grams: float) -> GeminiCallMetrics:
        """Crée une métrique avec paramètres cache et CO2 spécifiques."""
        impact_level = CarbonImpactLevel.EXCELLENT if co2_grams < 0.1 else CarbonImpactLevel.MODERATE
        
        return GeminiCallMetrics(
            call_id=f"test_cache_{cache_hit}",
            timestamp=datetime.now(),
            user_tier="premium",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            prompt_length=400,
            response_length=800,
            response_time_ms=1200,
            cache_hit=cache_hit,
            retry_count=0,
            estimated_co2_grams=co2_grams,
            carbon_impact_level=impact_level
        )
    
    def _create_metric_with_co2(self, co2_grams: float) -> GeminiCallMetrics:
        """Crée une métrique avec une valeur CO2 spécifique."""
        if co2_grams < 0.1:
            impact_level = CarbonImpactLevel.EXCELLENT
        elif co2_grams < 0.5:
            impact_level = CarbonImpactLevel.GOOD
        elif co2_grams < 2.0:
            impact_level = CarbonImpactLevel.MODERATE
        else:
            impact_level = CarbonImpactLevel.HIGH
        
        return GeminiCallMetrics(
            call_id=f"test_co2_{co2_grams}",
            timestamp=datetime.now(),
            user_tier="premium",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            prompt_length=400,
            response_length=800,
            response_time_ms=1200,
            cache_hit=True,
            retry_count=0,
            estimated_co2_grams=co2_grams,
            carbon_impact_level=impact_level
        )


class TestGeminiCallTracker:
    """Tests du tracker d'appels Gemini."""
    
    def test_tracker_initialization(self):
        """Test initialisation du tracker."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000.0)
        
        assert tracker.call_id == "test_001"
        assert tracker.user_tier == "premium"
        assert tracker.feature_used == "letter"
        assert not tracker.is_completed()
    
    def test_record_request(self):
        """Test enregistrement requête."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000.0)
        
        prompt = "Generate a cover letter for software engineer position"
        tracker.record_request(prompt)
        
        assert tracker.prompt_length == len(prompt)
        assert tracker.input_tokens > 0
    
    def test_record_response(self):
        """Test enregistrement réponse."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000.0)
        
        response = "Dear Hiring Manager, " * 20  # Réponse de taille raisonnable
        tracker.record_response(response, from_cache=True)
        
        assert tracker.response_length == len(response)
        assert tracker.output_tokens > 0
        assert tracker.total_tokens > 0
        assert tracker.cache_hit is True
        assert tracker.is_completed()
    
    def test_record_retries(self):
        """Test enregistrement des retries."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000.0)
        
        tracker.record_retry()
        tracker.record_retry()
        
        assert tracker.retry_count == 2
    
    def test_token_estimation(self):
        """Test estimation du nombre de tokens."""
        tracker = GeminiCallTracker("test_001", "premium", "letter", 1000.0)
        
        # Test avec texte français typique
        french_text = "Bonjour, je souhaite postuler pour le poste d'ingénieur logiciel dans votre entreprise."
        estimated_tokens = tracker._estimate_tokens(french_text)
        
        # Vérification estimation raisonnable (environ 1 token par 0.75 mots)
        word_count = len(french_text.split())
        expected_tokens = int(word_count / 0.75)
        
        assert abs(estimated_tokens - expected_tokens) <= 2  # Tolérance de 2 tokens