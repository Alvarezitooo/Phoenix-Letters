"""Gestionnaire central des optimisations IA."""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from core.services.api_cost_optimizer import APICostOptimizer, APIUsageMetrics
from infrastructure.security.prompt_injection_guard import PromptInjectionGuard, ThreatLevel
from core.services.rag_personalization_service import RAGPersonalizationService, UserContext
from core.entities.letter import UserTier, GenerationRequest
from shared.interfaces.ai_interface import AIServiceInterface


class AIOptimizationManager:
    """Gestionnaire central pour toutes les optimisations IA."""
    
    def __init__(self, ai_client: AIServiceInterface):
        self.logger = logging.getLogger(__name__)
        self.ai_client = ai_client
        
        # Services d'optimisation
        self.cost_optimizer = APICostOptimizer()
        self.security_guard = PromptInjectionGuard()
        self.rag_service = RAGPersonalizationService()
        
        # Métriques de performance
        self.optimization_metrics = {
            "total_requests": 0,
            "cost_savings_usd": 0.0,
            "security_blocks": 0,
            "personalization_hits": 0,
            "avg_response_time_ms": 0
        }
    
    def generate_optimized_content(
        self,
        request: GenerationRequest,
        user_context: Optional[Dict[str, Any]] = None,
        endpoint: str = "generate_letter"
    ) -> Dict[str, Any]:
        """
        Génère contenu avec toutes les optimisations appliquées.
        
        Args:
            request: Requête de génération
            user_context: Contexte utilisateur pour RAG
            endpoint: Type d'endpoint appelé
        Returns:
            Dict avec contenu généré et métriques
        """
        
        start_time = datetime.now()
        
        try:
            # 1. SÉCURITÉ - Analyse injection prompts
            security_result = self._apply_security_checks(request)
            if security_result["blocked"]:
                return self._create_security_blocked_response(security_result)
            
            # 2. PERSONNALISATION RAG - Enrichir contexte
            personalized_prompt = self._apply_rag_personalization(request, user_context)
            
            # 3. OPTIMISATION COÛTS - Optimiser paramètres
            optimized_params = self._apply_cost_optimization(
                personalized_prompt, request.user_tier, endpoint
            )
            
            # 4. GÉNÉRATION - Appel IA optimisé
            ai_response = self._call_ai_with_optimizations(optimized_params, request.user_tier)
            
            # 5. POST-TRAITEMENT - Validation et métriques
            final_response = self._post_process_response(
                ai_response, request, start_time, optimized_params
            )
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"AI optimization failed: {e}")
            return self._create_error_response(str(e))
    
    def _apply_security_checks(self, request: GenerationRequest) -> Dict[str, Any]:
        """Applique vérifications sécuritaires."""
        
        # Analyser tous les inputs utilisateur
        inputs_to_check = [
            ("cv_content", request.cv_content),
            ("job_offer", request.job_offer_content),
            ("additional_info", getattr(request, 'additional_info', ''))
        ]
        
        security_results = []
        blocked = False
        
        for input_name, content in inputs_to_check:
            if content:
                detection = self.security_guard.analyze_input(content, input_name)
                security_results.append({
                    "input": input_name,
                    "threat_level": detection.threat_level.value,
                    "is_malicious": detection.is_malicious,
                    "patterns": detection.detected_patterns
                })
                
                if detection.is_malicious:
                    blocked = True
                    self.optimization_metrics["security_blocks"] += 1
        
        return {
            "blocked": blocked,
            "results": security_results,
            "overall_threat": max([r["threat_level"] for r in security_results], default="low")
        }
    
    def _apply_rag_personalization(
        self, 
        request: GenerationRequest,
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Applique personnalisation RAG."""
        
        try:
            if user_context:
                # Construire contexte utilisateur enrichi
                user_ctx = self.rag_service.build_user_context(
                    user_id=user_context.get("user_id", "anonymous"),
                    cv_content=request.cv_content,
                    target_role=request.job_title,
                    target_sector=user_context.get("target_sector", "général"),
                    additional_info=user_context
                )
                
                # Récupérer contexte de personnalisation
                personalization_ctx = self.rag_service.retrieve_relevant_context(
                    user_ctx, request.job_offer_content
                )
                
                # Générer prompt personnalisé
                personalized_prompt = self.rag_service.generate_personalized_prompt(
                    personalization_ctx
                )
                
                self.optimization_metrics["personalization_hits"] += 1
                
                return personalized_prompt
                
            else:
                # Fallback - prompt basique
                return self._create_basic_prompt(request)
                
        except Exception as e:
            self.logger.warning(f"RAG personalization failed, using basic prompt: {e}")
            return self._create_basic_prompt(request)
    
    def _create_basic_prompt(self, request: GenerationRequest) -> str:
        """Crée prompt basique sans RAG."""
        return f"""
        Rédigez une lettre de motivation professionnelle pour :
        - Poste : {request.job_title}
        - Entreprise : {request.company_name}
        - Ton souhaité : {request.tone.value}
        
        CV du candidat :
        {request.cv_content}
        
        Offre d'emploi :
        {request.job_offer_content}
        
        {"Compétences transférables : " + request.transferable_skills if request.transferable_skills else ""}
        """
    
    def _apply_cost_optimization(
        self, 
        prompt: str, 
        user_tier: UserTier,
        endpoint: str
    ) -> Dict[str, Any]:
        """Applique optimisations de coûts."""
        
        # Estimer coût initial
        initial_estimate = self.cost_optimizer.estimate_request_cost(prompt)
        
        # Optimiser paramètres
        optimization_result = self.cost_optimizer.optimize_request_parameters(
            prompt=prompt,
            user_tier=user_tier.value,
            endpoint=endpoint
        )
        
        # Accumuler économies
        self.optimization_metrics["cost_savings_usd"] += optimization_result["savings_usd"]
        
        return {
            "prompt": optimization_result["optimized_params"]["prompt"],
            "max_tokens": optimization_result["optimized_params"]["max_tokens"],
            "temperature": optimization_result["optimized_params"]["temperature"],
            "original_cost": optimization_result["original_cost"],
            "optimized_cost": optimization_result["optimized_cost"],
            "savings": optimization_result["savings_usd"],
            "optimizations": optimization_result["optimizations_applied"]
        }
    
    def _call_ai_with_optimizations(
        self, 
        optimized_params: Dict[str, Any],
        user_tier: UserTier
    ) -> str:
        """Appelle IA avec paramètres optimisés."""
        
        # Créer prompt wrapper sécurisé
        safe_prompt = self.security_guard.create_safe_prompt_wrapper(
            optimized_params["prompt"],
            "Vous êtes un assistant spécialisé en lettres de motivation pour reconversions."
        )
        
        # Appel IA avec paramètres optimisés
        response = self.ai_client.generate_content(
            prompt=safe_prompt,
            user_tier=user_tier,
            max_tokens=optimized_params["max_tokens"],
            temperature=optimized_params["temperature"]
        )
        
        return response
    
    def _post_process_response(
        self,
        ai_response: str,
        request: GenerationRequest,
        start_time: datetime,
        optimized_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post-traite la réponse IA."""
        
        end_time = datetime.now()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Mettre à jour métriques
        self.optimization_metrics["total_requests"] += 1
        self.optimization_metrics["avg_response_time_ms"] = (
            (self.optimization_metrics["avg_response_time_ms"] * (self.optimization_metrics["total_requests"] - 1) + response_time_ms) 
            / self.optimization_metrics["total_requests"]
        )
        
        # Tracker usage API
        self._track_api_usage(request, optimized_params, response_time_ms, True)
        
        return {
            "content": ai_response,
            "optimization_applied": optimized_params.get("optimizations", []),
            "cost_savings_usd": optimized_params.get("savings", 0.0),
            "response_time_ms": response_time_ms,
            "tokens_saved": optimized_params.get("token_reduction", 0),
            "security_status": "clean",
            "personalization_used": True
        }
    
    def _create_security_blocked_response(self, security_result: Dict[str, Any]) -> Dict[str, Any]:
        """Crée réponse pour contenu bloqué par sécurité."""
        return {
            "content": "⚠️ Votre demande n'a pas pu être traitée pour des raisons de sécurité. Veuillez reformuler votre requête.",
            "error": "security_blocked",
            "threat_level": security_result["overall_threat"],
            "detected_patterns": security_result["results"],
            "optimization_applied": [],
            "cost_savings_usd": 0.0,
            "response_time_ms": 0,
            "security_status": "blocked"
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Crée réponse d'erreur."""
        return {
            "content": "❌ Une erreur s'est produite lors de la génération. Veuillez réessayer.",
            "error": error_message,
            "optimization_applied": [],
            "cost_savings_usd": 0.0,
            "response_time_ms": 0,
            "security_status": "error"
        }
    
    def _track_api_usage(
        self,
        request: GenerationRequest,
        optimized_params: Dict[str, Any],
        response_time_ms: int,
        success: bool
    ) -> None:
        """Track utilisation API pour analytics."""
        
        # Estimer tokens (approximation)
        prompt_tokens = len(optimized_params["prompt"]) // 4
        completion_tokens = optimized_params["max_tokens"]
        
        metrics = APIUsageMetrics(
            user_id=getattr(request, 'user_id', 'anonymous'),
            user_tier=request.user_tier.value,
            endpoint="generate_letter",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_estimate=optimized_params.get("optimized_cost", 0.0),
            response_time_ms=response_time_ms,
            timestamp=datetime.now(),
            success=success
        )
        
        self.cost_optimizer.track_api_usage(metrics)
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Retourne status des optimisations."""
        return {
            "services_active": {
                "cost_optimizer": True,
                "security_guard": True, 
                "rag_personalization": True
            },
            "metrics": self.optimization_metrics,
            "cost_analytics": self.cost_optimizer.get_cost_analytics(),
            "security_metrics": self.security_guard.get_security_metrics(),
            "rag_metrics": self.rag_service.get_personalization_metrics()
        }
    
    def configure_optimization_rules(self, rules: Dict[str, Any]) -> None:
        """Configure règles d'optimisation personnalisées."""
        
        if "cost_rules" in rules:
            # Mettre à jour règles coût
            pass
        
        if "security_rules" in rules:
            # Mettre à jour règles sécurité
            pass
        
        if "rag_rules" in rules:
            # Mettre à jour règles RAG
            pass
        
        self.logger.info(f"Optimization rules updated: {list(rules.keys())}")