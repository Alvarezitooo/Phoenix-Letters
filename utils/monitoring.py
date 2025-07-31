# ==============================================================================
# MONITORING D'URGENCE - PHOENIX LETTERS
# Découvrir QUI et QUOI consomme tes requêtes API
# ==============================================================================

import streamlit as st
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

# ==============================================================================
# 1. TRACKING DES REQUÊTES EN TEMPS RÉEL
# ==============================================================================

class APIUsageTracker:
    """Traque chaque appel API pour identifier les gros consommateurs."""
    
    def __init__(self):
        if 'api_tracker' not in st.session_state:
            st.session_state.api_tracker = {
                'calls_history': [],
                'users_activity': defaultdict(list),
                'functions_called': Counter(),
                'total_calls_today': 0,
                'cost_estimate': 0.0
            }
    
    def log_api_call(self, 
                    function_name: str, 
                    user_id: str = None, 
                    prompt_length: int = 0,
                    response_length: int = 0,
                    cached: bool = False):
        """Enregistre chaque appel API avec détails."""
        
        timestamp = datetime.now()
        user_id = user_id or self._get_anonymous_user_id()
        
        call_info = {
            'timestamp': timestamp.isoformat(),
            'function': function_name,
            'user_id': user_id,
            'prompt_length': prompt_length,
            'response_length': response_length,
            'cached': cached,
            'estimated_cost': self._estimate_cost(prompt_length, response_length)
        }
        
        # Stockage en session
        st.session_state.api_tracker['calls_history'].append(call_info)
        st.session_state.api_tracker['users_activity'][user_id].append(call_info)
        st.session_state.api_tracker['functions_called'][function_name] += 1
        
        if not cached:
            st.session_state.api_tracker['total_calls_today'] += 1
            st.session_state.api_tracker['cost_estimate'] += call_info['estimated_cost']
        
        # Log pour debugging
        status = " CACHED" if cached else " API CALL"
        logging.info(f"{status} | {function_name} | User: {user_id[:8]} | Cost: ${call_info['estimated_cost']:.4f}")
    
    def _get_anonymous_user_id(self) -> str:
        """Génère un ID utilisateur anonyme mais persistant."""
        if 'user_anonymous_id' not in st.session_state:
            import hashlib
            import time
            # Utilise l'IP + timestamp de session pour créer un ID unique
            session_start = str(time.time())
            st.session_state.user_anonymous_id = hashlib.md5(session_start.encode()).hexdigest()[:12]
        return st.session_state.user_anonymous_id
    
    def _estimate_cost(self, prompt_length: int, response_length: int) -> float:
        """Estime le coût approximatif d'un appel Gemini."""
        # Coûts approximatifs Gemini (à ajuster selon tes tarifs réels)
        input_cost_per_1k = 0.00015  # $0.00015 per 1K input tokens
        output_cost_per_1k = 0.0006  # $0.0006 per 1K output tokens
        
        # Approximation : 4 caractères = 1 token
        input_tokens = prompt_length / 4
        output_tokens = response_length / 4
        
        cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)
        return cost

# ==============================================================================
# 2. WRAPPER POUR TES FONCTIONS EXISTANTES - À AJOUTER PARTOUT
# ==============================================================================

def track_api_call(function_name: str):
    """Décorateur pour tracker automatiquement les appels API."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracker = APIUsageTracker()
            start_time = time.time()
            
            # Essaie d'extraire des infos sur le prompt
            prompt_length = 0
            if 'prompt' in kwargs:
                prompt_length = len(str(kwargs['prompt']))
            elif len(args) > 0 and isinstance(args[0], str):
                prompt_length = len(args[0])
            
            try:
                # Appel de la fonction
                result = func(*args, **kwargs)
                response_length = len(str(result)) if result else 0
                
                # Détecte si c'était caché (temps très rapide = cache)
                execution_time = time.time() - start_time
                was_cached = execution_time < 0.1  # Si moins de 100ms = probablement cache
                
                # Log l'appel
                tracker.log_api_call(
                    function_name=function_name,
                    prompt_length=prompt_length,
                    response_length=response_length,
                    cached=was_cached
                )
                
                return result
                
            except Exception as e:
                # Log même les erreurs
                tracker.log_api_call(
                    function_name=f"{function_name}_ERROR",
                    prompt_length=prompt_length,
                    response_length=0,
                    cached=False
                )
                raise e
        return wrapper
    return decorator

# ==============================================================================
# 3. DASHBOARD DE MONITORING TEMPS RÉEL
# ==============================================================================

def render_api_monitoring_dashboard():
    """Dashboard de monitoring à ajouter dans ton app."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("###  API Monitoring")
    
    if 'api_tracker' not in st.session_state:
        st.sidebar.info("Aucune donnée de tracking disponible")
        return
    
    tracker_data = st.session_state.api_tracker
    
    # Statistiques rapides
    total_calls = tracker_data['total_calls_today']
    cached_calls = len([c for c in tracker_data['calls_history'] if c['cached']])
    cost_today = tracker_data['cost_estimate']
    
    st.sidebar.metric(" Appels API aujourd'hui", total_calls)
    st.sidebar.metric("⚡ Appels en cache", cached_calls)
    st.sidebar.metric(" Coût estimé", f"${cost_today:.4f}")
    
    # Alerte si trop de requêtes
    if total_calls > 30:
        st.sidebar.error(f"⚠️ {total_calls} appels API ! Cache nécessaire")
    elif total_calls > 15:
        st.sidebar.warning(f"⚡ {total_calls} appels API. Surveillance recommandée")
    
    # Bouton pour voir les détails
    if st.sidebar.button(" Voir Détails Complets"):
        st.session_state.show_monitoring_details = True

def render_detailed_monitoring():
    """Dashboard détaillé des appels API."""
    
    if not st.session_state.get('show_monitoring_details', False):
        return
    
    st.markdown("##  Monitoring API Détaillé")
    
    tracker_data = st.session_state.api_tracker
    calls_history = tracker_data['calls_history']
    
    if not calls_history:
        st.info("Aucun appel API enregistré")
        return
    
    # Analyse par fonction
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("###  Top Fonctions Appelées")
        functions_count = tracker_data['functions_called']
        for func, count in functions_count.most_common(5):
            st.write(f"- **{func}**: {count} appels")
    
    with col2:
        st.markdown("###  Activité Utilisateurs")
        users_activity = tracker_data['users_activity']
        for user_id, activities in list(users_activity.items())[:5]:
            st.write(f"- **User {user_id[:8]}**: {len(activities)} appels")
    
    # Timeline des appels récents
    st.markdown("### ⏰ Timeline des 20 derniers appels")
    recent_calls = sorted(calls_history, key=lambda x: x['timestamp'], reverse=True)[:20]
    
    for call in recent_calls:
        timestamp = datetime.fromisoformat(call['timestamp'])
        status_icon = "" if call['cached'] else ""
        cost = call['estimated_cost']
        
        st.write(f"{status_icon} {timestamp.strftime('%H:%M:%S')} | "
                f"**{call['function']}** | "
                f"User: {call['user_id'][:8]} | "
                f"${cost:.4f}")
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("️ Reset Monitoring"):
            st.session_state.api_tracker = {
                'calls_history': [],
                'users_activity': defaultdict(list),
                'functions_called': Counter(),
                'total_calls_today': 0,
                'cost_estimate': 0.0
            }
            st.success("Monitoring reset !")
    
    with col2:
        if st.button(" Export Data"):
            export_data = json.dumps(calls_history, indent=2)
            st.download_button(
                " Download JSON",
                export_data,
                "phoenix_api_monitoring.json",
                "application/json"
            )
    
    with col3:
        if st.button("❌ Fermer"):
            st.session_state.show_monitoring_details = False

# ==============================================================================
# 4. MODIFICATION DE TES FONCTIONS EXISTANTES - EXEMPLE
# ==============================================================================

# AVANT (tes fonctions actuelles)
# def suggerer_competences_transferables(ancien_domaine, nouveau_domaine):
#     # ... ton code ...

# APRÈS (avec tracking automatique)
# @track_api_call("suggerer_competences_transferables") @st.cache_data(ttl=3600)
# def suggerer_competences_transferables_tracked(ancien_domaine: str, nouveau_domaine: str):
#     """Version avec tracking automatique."""
#     # Ton code existant ici
#     from infrastructure.ai.gemini_client import GeminiClient
    
#     client = GeminiClient()
#     prompt = f"Suggérer compétences transférables de {ancien_domaine} vers {nouveau_domaine}"
    
#     response = client.generate_content(
#         prompt=prompt,
#         user_tier="FREE",
#         max_tokens=500
#     )
    
#     return response

# ==============================================================================
# 5. DIAGNOSTIC IMMÉDIAT - À AJOUTER DANS TON APP.PY
# ==============================================================================

def diagnostic_urgence_50_requetes():
    """Diagnostic pour comprendre d'où viennent tes 50 requêtes."""
    
    st.markdown("##  Diagnostic Urgence - 50 Requêtes")
    
    # Test de simulation de charge
    if st.button(" Simuler 10 utilisateurs"):
        with st.spinner("Simulation en cours..."):
            tracker = APIUsageTracker()
            
            # Simule 10 utilisateurs faisant chacun 3 actions
            for user_num in range(10):
                for action in ['generer_lettre', 'suggerer_competences', 'analyser_culture']:
                    tracker.log_api_call(
                        function_name=action,
                        user_id=f"user_test_{user_num}",
                        prompt_length=800,
                        response_length=400,
                        cached=user_num > 5  # Les 5 premiers ne sont pas cachés
                    )
        
        st.success("✅ Simulation terminée ! Regarde le monitoring dans la sidebar.")
    
    # Analyse des patterns courants
    st.markdown("###  Patterns Courants de Consommation API")
    
    patterns = {
        " Rechargement de page": "Chaque F5 = nouvelle requête sans cache",
        " Plusieurs utilisateurs": "Chaque nouvel utilisateur teste l'app",
        " Même fonctionnalité": "Plusieurs clics sur 'Générer' sans cache",
        " Multi-devices": "Un utilisateur teste sur phone + desktop",
        " Bots/crawlers": "Des robots indexent ton site"
    }
    
    for pattern, description in patterns.items():
        st.write(f"{pattern} **{description}**")
    
    # Recommandations immédiates
    st.markdown("### ⚡ Actions Immédiates Recommandées")
    
    actions = [
        "✅ **Implémenter le cache** (réduction 80% des appels)",
        " **Activer le monitoring** (code ci-dessus)",
        " **Rate limiting par IP** (max 10 requêtes/heure pour FREE)",
        " **Auth simple** (même juste un nom) pour tracker les vrais users",
        " **Alertes budget** dans Google Cloud Console"
    ]
    
    for action in actions:
        st.write(action)

# ==============================================================================
# 6. INTEGRATION DANS TON APP.PY PRINCIPAL
# ==============================================================================

def integrate_monitoring_in_main_app():
    """Code à ajouter dans ton app.py principal."""
    
    # En haut de ton app.py, après les imports
    from datetime import datetime
    
    # Initialize monitoring
    if 'app_start_time' not in st.session_state:
        st.session_state.app_start_time = datetime.now()
        APIUsageTracker()  # Initialize tracker
    
    # Dans ta sidebar (ou où tu veux)
    render_api_monitoring_dashboard()
    
    # Dans le body principal, conditionnellement
    render_detailed_monitoring()
    
    # Pour debugging uniquement (à retirer en prod)
    if st.checkbox(" Mode Debug - Diagnostic 50 Requêtes"):
        diagnostic_urgence_50_requetes()
