"""Service d'optimisation des coûts API Gemini."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
from collections import defaultdict


@dataclass
class APIUsageMetrics:
    """Métriques d'utilisation API."""
    user_id: str
    user_tier: str
    endpoint: str  # "generate_content", "analyze_culture", etc.
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: float
    response_time_ms: int
    timestamp: datetime
    success: bool
    model_used: str = "gemini-1.5-flash"


@dataclass 
class CostOptimizationRule:
    """Règle d'optimisation des coûts."""
    rule_id: str
    condition: str  # "token_count > 1000", "user_tier == free"
    action: str     # "compress_prompt", "cache_response", "use_smaller_model"
    savings_pct: float  # % d'économie estimée
    priority: int   # 1-5, 5 = highest


class APICostOptimizer:
    """Service d'optimisation des coûts d'API Gemini."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.usage_cache: Dict[str, List[APIUsageMetrics]] = defaultdict(list)
        self.optimization_rules = self._init_optimization_rules()
        
        # Prix Gemini 1.5 Flash (estimations)
        self.pricing = {
            "gemini-1.5-flash": {
                "input_token_cost": 0.000075,    # $0.075 per 1K tokens
                "output_token_cost": 0.000300,   # $0.30 per 1K tokens
            },
            "gemini-1.5-pro": {
                "input_token_cost": 0.00125,     # $1.25 per 1K tokens  
                "output_token_cost": 0.00375,    # $3.75 per 1K tokens
            }
        }
    
    def _init_optimization_rules(self) -> List[CostOptimizationRule]:
        """Initialise les règles d'optimisation."""
        return [
            CostOptimizationRule(
                rule_id="compress_long_prompts",
                condition="token_count > 1500",
                action="compress_prompt",
                savings_pct=0.25,
                priority=4
            ),
            
            CostOptimizationRule(
                rule_id="cache_repeated_requests",
                condition="similar_prompt_exists",
                action="use_cache",
                savings_pct=1.0,  # 100% économie si cache hit
                priority=5
            ),
            
            CostOptimizationRule(
                rule_id="batch_free_users",
                condition="user_tier == free AND queue_length < 5",
                action="batch_request",
                savings_pct=0.15,
                priority=3
            ),
            
            CostOptimizationRule(
                rule_id="lower_temperature_analysis",
                condition="endpoint == analysis AND temperature > 0.3",
                action="reduce_temperature",
                savings_pct=0.10,
                priority=2
            ),
            
            CostOptimizationRule(
                rule_id="smart_token_limit",
                condition="user_tier == free",
                action="optimize_max_tokens",
                savings_pct=0.20,
                priority=3
            )
        ]
    
    def estimate_request_cost(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        model: str = "gemini-1.5-flash"
    ) -> Dict[str, Any]:
        """
        Estime le coût d'une requête avant exécution.
        
        Args:
            prompt: Prompt à analyser
            max_tokens: Tokens max de réponse
            model: Modèle à utiliser
        Returns:
            Dict avec estimation coût et métriques
        """
        
        # Estimation tokens input (approximation: 1 token ≈ 4 chars)
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = max_tokens
        
        model_pricing = self.pricing.get(model, self.pricing["gemini-1.5-flash"])
        
        input_cost = (estimated_input_tokens / 1000) * model_pricing["input_token_cost"]
        output_cost = (estimated_output_tokens / 1000) * model_pricing["output_token_cost"]
        total_cost = input_cost + output_cost
        
        return {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": total_cost,
            "model": model,
            "optimization_potential": self._calculate_optimization_potential(
                estimated_input_tokens + estimated_output_tokens, prompt
            )
        }
    
    def optimize_request_parameters(
        self,
        prompt: str,
        user_tier: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        endpoint: str = "generate_content"
    ) -> Dict[str, Any]:
        """
        Optimise les paramètres de requête pour réduire les coûts.
        
        Returns:
            Dict avec paramètres optimisés et économies estimées
        """
        
        original_estimate = self.estimate_request_cost(prompt, max_tokens)
        optimizations_applied = []
        total_savings = 0.0
        
        optimized_params = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Appliquer règles d'optimisation
        for rule in sorted(self.optimization_rules, key=lambda r: r.priority, reverse=True):
            if self._evaluate_rule_condition(rule, prompt, user_tier, max_tokens, endpoint):
                
                if rule.action == "compress_prompt":
                    optimized_params["prompt"] = self._compress_prompt(prompt)
                    optimizations_applied.append("prompt_compression")
                    total_savings += rule.savings_pct
                
                elif rule.action == "optimize_max_tokens":
                    # Réduire max_tokens pour users Free
                    if user_tier == "free":
                        optimized_params["max_tokens"] = min(max_tokens, 800)
                        optimizations_applied.append("token_limit_optimization")
                        total_savings += rule.savings_pct
                
                elif rule.action == "reduce_temperature":
                    # Température plus basse pour analyses (plus déterministe, moins de tokens)
                    if endpoint in ["analysis", "ats_analyzer", "smart_coach"]:
                        optimized_params["temperature"] = min(temperature, 0.3)
                        optimizations_applied.append("temperature_reduction")
                        total_savings += rule.savings_pct
        
        # Calculer économies réelles
        optimized_estimate = self.estimate_request_cost(
            optimized_params["prompt"], 
            optimized_params["max_tokens"]
        )
        
        actual_savings = original_estimate["total_cost_usd"] - optimized_estimate["total_cost_usd"]
        savings_percentage = (actual_savings / original_estimate["total_cost_usd"]) * 100 if original_estimate["total_cost_usd"] > 0 else 0
        
        return {
            "optimized_params": optimized_params,
            "original_cost": original_estimate["total_cost_usd"],
            "optimized_cost": optimized_estimate["total_cost_usd"],
            "savings_usd": actual_savings,
            "savings_percentage": savings_percentage,
            "optimizations_applied": optimizations_applied,
            "token_reduction": original_estimate["estimated_total_tokens"] - optimized_estimate["estimated_total_tokens"]
        }
    
    def _evaluate_rule_condition(
        self, 
        rule: CostOptimizationRule, 
        prompt: str, 
        user_tier: str, 
        max_tokens: int,
        endpoint: str
    ) -> bool:
        """Évalue si une règle d'optimisation s'applique."""
        
        condition = rule.condition
        token_count = len(prompt) // 4  # Estimation approximative
        
        # Évaluation des conditions
        if "token_count > 1500" in condition:
            return token_count > 1500
        
        elif "user_tier == free" in condition:
            return user_tier == "free"
        
        elif "endpoint == analysis" in condition:
            return endpoint in ["analysis", "ats_analyzer", "smart_coach", "mirror_match"]
        
        elif "similar_prompt_exists" in condition:
            return self._check_prompt_similarity(prompt)
        
        return False
    
    def _compress_prompt(self, prompt: str) -> str:
        """Compresse un prompt long tout en gardant l'essence."""
        
        # Techniques de compression intelligente
        compressed = prompt
        
        # 1. Supprimer répétitions
        lines = compressed.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            line_clean = line.strip()
            if line_clean and line_clean not in seen:
                unique_lines.append(line)
                seen.add(line_clean)
        compressed = '\n'.join(unique_lines)
        
        # 2. Raccourcir phrases longues (garder essentiels)
        if len(compressed) > 2000:
            # Garder introduction + instructions essentielles + contexte minimal
            parts = compressed.split('\n\n')
            if len(parts) > 3:
                compressed = '\n\n'.join([parts[0], parts[1], parts[-1]])
        
        # 3. Remplacer expressions longues par versions courtes
        replacements = {
            "lettre de motivation": "lettre",
            "Veuillez rédiger": "Rédigez",
            "Il est important de": "Important:",
            "Assurez-vous que": "Vérifiez:",
            "en prenant en compte": "avec",
            "par conséquent": "donc"
        }
        
        for long_form, short_form in replacements.items():
            compressed = compressed.replace(long_form, short_form)
        
        return compressed
    
    def _check_prompt_similarity(self, prompt: str, threshold: float = 0.8) -> bool:
        """Vérifie si un prompt similaire existe dans le cache."""
        # Implémentation simplifiée - à améliorer avec embeddings
        prompt_words = set(prompt.lower().split())
        
        for cached_metrics_list in self.usage_cache.values():
            for metrics in cached_metrics_list[-10:]:  # Check last 10 requests
                # Récupérer prompt du cache (à implémenter)
                # cached_prompt_words = set(cached_prompt.lower().split())
                # similarity = len(prompt_words & cached_prompt_words) / len(prompt_words | cached_prompt_words)
                # if similarity > threshold:
                #     return True
                pass
        
        return False
    
    def _calculate_optimization_potential(self, total_tokens: int, prompt: str) -> Dict[str, float]:
        """Calcule le potentiel d'optimisation."""
        
        potential = {}
        
        # Potentiel compression
        if len(prompt) > 1500:
            potential["compression"] = min(0.30, (len(prompt) - 1500) / len(prompt))
        
        # Potentiel réduction tokens
        if total_tokens > 1200:
            potential["token_reduction"] = min(0.25, (total_tokens - 1200) / total_tokens)
        
        # Potentiel caching
        potential["caching"] = 0.15  # Économie moyenne avec cache
        
        return potential
    
    def track_api_usage(self, metrics: APIUsageMetrics) -> None:
        """Track l'utilisation API pour analytics."""
        
        self.usage_cache[metrics.user_id].append(metrics)
        
        # Garder seulement les 100 derniers par utilisateur
        if len(self.usage_cache[metrics.user_id]) > 100:
            self.usage_cache[metrics.user_id] = self.usage_cache[metrics.user_id][-100:]
        
        # Log pour monitoring
        self.logger.info(f"API Usage: {asdict(metrics)}")
    
    def get_cost_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retourne analytics de coûts."""
        
        if user_id:
            user_metrics = self.usage_cache.get(user_id, [])
            total_cost = sum(m.cost_estimate for m in user_metrics)
            total_tokens = sum(m.total_tokens for m in user_metrics)
            
            return {
                "user_id": user_id,
                "total_requests": len(user_metrics),
                "total_cost_usd": total_cost,
                "total_tokens": total_tokens,
                "avg_cost_per_request": total_cost / len(user_metrics) if user_metrics else 0,
                "last_30_days": self._get_recent_usage(user_metrics, days=30)
            }
        
        # Analytics globales
        all_metrics = []
        for metrics_list in self.usage_cache.values():
            all_metrics.extend(metrics_list)
        
        return {
            "total_users": len(self.usage_cache),
            "total_requests": len(all_metrics),
            "total_cost_usd": sum(m.cost_estimate for m in all_metrics),
            "avg_tokens_per_request": sum(m.total_tokens for m in all_metrics) / len(all_metrics) if all_metrics else 0,
            "cost_by_tier": self._get_cost_by_tier(all_metrics),
            "top_expensive_endpoints": self._get_top_expensive_endpoints(all_metrics)
        }
    
    def _get_recent_usage(self, metrics: List[APIUsageMetrics], days: int) -> Dict[str, Any]:
        """Récupère usage récent."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = [m for m in metrics if m.timestamp > cutoff]
        
        return {
            "requests": len(recent),
            "cost_usd": sum(m.cost_estimate for m in recent),
            "tokens": sum(m.total_tokens for m in recent)
        }
    
    def _get_cost_by_tier(self, metrics: List[APIUsageMetrics]) -> Dict[str, float]:
        """Coût par tier utilisateur."""
        cost_by_tier = defaultdict(float)
        for m in metrics:
            cost_by_tier[m.user_tier] += m.cost_estimate
        return dict(cost_by_tier)
    
    def _get_top_expensive_endpoints(self, metrics: List[APIUsageMetrics]) -> List[Dict[str, Any]]:
        """Endpoints les plus coûteux."""
        cost_by_endpoint = defaultdict(float)
        count_by_endpoint = defaultdict(int)
        
        for m in metrics:
            cost_by_endpoint[m.endpoint] += m.cost_estimate
            count_by_endpoint[m.endpoint] += 1
        
        return [
            {
                "endpoint": endpoint,
                "total_cost": cost,
                "avg_cost": cost / count_by_endpoint[endpoint],
                "request_count": count_by_endpoint[endpoint]
            }
            for endpoint, cost in sorted(cost_by_endpoint.items(), key=lambda x: x[1], reverse=True)
        ]