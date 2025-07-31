# 🏗️ ARCHITECTURE AUTHENTIFICATION PHOENIX LETTERS
## Roadmap Sentier 2 - Fondations pour l'Avenir

### ✅ **PHASE 1-3 COMPLÉTÉES par Claude Code**

#### 📊 **Architecture Actuelle Analysée**
- **Gestion utilisateur** : `st.session_state` + `SessionManager` (volatile)
- **User ID** : UUID temporaire généré par session (pas de persistance)
- **Tiers** : `UserTier` enum (FREE/PREMIUM/PREMIUM_PLUS) 
- **Limitations** : Pas d'auth réelle, beta tester mode, perte données fermeture navigateur

#### 🏛️ **Modèle Utilisateur Conçu**
- **Entités** : `User`, `UserProfile`, `UserPreferences`, `UserSubscription`, `UserUsageStats`, `UserSession`
- **Schéma DB PostgreSQL** : Tables complètes avec indexes, triggers, RLS
- **Sécurité** : Auth logs, suspicious activities, cleanup automatique

#### 🔐 **Infrastructure JWT Créée**
- **JWTManager** : Access tokens (15min), Refresh tokens (30j)
- **Types tokens** : Email verification, password reset
- **Sécurité** : Blacklist, bcrypt, token rotation

---

### 🚀 **PHASES RESTANTES - À CONTINUER AVEC GEMINI CLI**

#### **PHASE 4 : UserAuthService** [HIGH PRIORITY]
```python
# Fichier à créer : infrastructure/auth/user_auth_service.py
class UserAuthService:
    def register_user(email, password, profile_data) -> User
    def authenticate_user(email, password) -> tuple[User, str, str]  # user, access, refresh
    def verify_email(token) -> bool
    def reset_password(email) -> str  # token
    def change_password(user_id, old_pass, new_pass) -> bool
    def get_user_by_id(user_id) -> User
    def update_user_profile(user_id, profile_data) -> User
    def deactivate_user(user_id) -> bool
```

#### **PHASE 5 : Middleware Streamlit** [MEDIUM PRIORITY]
```python
# Fichier à créer : infrastructure/auth/streamlit_auth_middleware.py
class StreamlitAuthMiddleware:
    def require_auth(func) -> callable  # Décorateur
    def require_tier(tier: UserTier) -> callable  # Décorateur
    def get_current_user() -> Optional[User]
    def login_form() -> Optional[User]
    def logout() -> None
    def check_session_validity() -> bool
```

#### **PHASE 6 : Migration Tiers** [MEDIUM PRIORITY]
- Remplacer `st.session_state.user_tier` par `current_user.subscription.current_tier`
- Adapter `UserLimitManager` pour utiliser DB au lieu de session
- Migrer logique dans `app.py`, `generator_page.py`, tous les services Premium

#### **PHASE 7 : Sécurité Avancée** [LOW PRIORITY]
- Password policies (longueur, complexité, historique)
- 2FA avec TOTP (Google Authenticator)
- Rate limiting sur auth endpoints
- Détection activités suspectes

#### **PHASE 8 : Tests & Validation** [MEDIUM PRIORITY]
- Tests unitaires services auth
- Tests intégration middleware Streamlit
- Tests sécurité (injections, brute force)
- Documentation API auth

---

### 🎯 **MIGRATION STRATEGY**

#### **Étape 1 : Mode Coexistence**
```python
# Dans app.py - Transition douce
if AUTH_ENABLED:
    user = auth_middleware.get_current_user()
    user_tier = user.subscription.current_tier if user else UserTier.FREE
else:
    # Mode legacy actuel
    user_tier = st.session_state.get('user_tier', UserTier.FREE)
```

#### **Étape 2 : UI Auth Components**
- Pages : login, register, forgot-password, profile
- Composants : login form, user menu, subscription status
- Intégration dans navigation actuelle

#### **Étape 3 : Database Setup**
- Exécuter `infrastructure/database/schema.sql`
- Configuration connexion PostgreSQL
- Variables environnement sécurisées

---

### 📚 **FICHIERS CRÉÉS**

1. **`core/entities/user.py`** ✅
   - Entités User complètes avec profile, subscription, stats
   - Validation, méthodes utilitaires, serialization

2. **`infrastructure/database/schema.sql`** ✅
   - Schema PostgreSQL complet production-ready
   - 9 tables avec indexes, triggers, fonctions maintenance
   - Row Level Security, audit logs, permissions

3. **`infrastructure/auth/jwt_manager.py`** ✅
   - Gestion JWT sécurisée multi-types tokens
   - Bcrypt password hashing, blacklist support
   - Refresh token rotation, claims personnalisés

---

### 🎪 **NEXT STEPS POUR GEMINI CLI**

1. **Commencer par PHASE 4** : `UserAuthService` - Le cœur du système
2. **Créer DB de test** : Exécuter schema.sql sur PostgreSQL local
3. **Middleware Streamlit** : Intégration auth dans UI existante
4. **Migration progressive** : Remplacer session_state par DB queries

### 🛡️ **SÉCURITÉ MAINTENUE**
- **Mock API toujours actif** - Aucune consommation Gemini
- **Architecture non-intrusive** - Pas de breaking changes
- **Migration progressive** - Coexistence ancien/nouveau système

**📞 Ready for Gemini CLI handover!** 🚀