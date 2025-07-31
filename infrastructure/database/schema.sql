-- Phoenix Letters - Schéma Base de Données Authentication
-- Version: 1.0
-- DevSecOps: Claude Phoenix Guardian

-- =============================================================================
-- TABLES PRINCIPALES
-- =============================================================================

-- Table utilisateurs principale
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    newsletter_opt_in BOOLEAN DEFAULT FALSE,
    
    -- Authentification
    auth_provider VARCHAR(20) NOT NULL DEFAULT 'email' CHECK (auth_provider IN ('email', 'google', 'github', 'linkedin')),
    provider_id VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    
    -- Statut et dates
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'banned', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Sécurité
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    
    -- Contraintes
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_-]{3,30}$')
);

-- Table profils utilisateurs
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    professional_domain VARCHAR(100),
    target_domain VARCHAR(100),
    experience_years INTEGER CHECK (experience_years >= 0 AND experience_years <= 60),
    location VARCHAR(100),
    linkedin_url VARCHAR(255),
    avatar_url VARCHAR(500),
    bio TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table préférences utilisateurs
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'fr',
    timezone VARCHAR(50) DEFAULT 'Europe/Paris',
    email_notifications BOOLEAN DEFAULT TRUE,
    marketing_emails BOOLEAN DEFAULT FALSE,
    theme VARCHAR(20) DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'auto')),
    default_tone VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table abonnements utilisateurs
CREATE TABLE user_subscriptions (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_tier VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (current_tier IN ('free', 'premium', 'premium_plus')),
    subscription_start TIMESTAMP WITH TIME ZONE,
    subscription_end TIMESTAMP WITH TIME ZONE,
    auto_renewal BOOLEAN DEFAULT FALSE,
    payment_method VARCHAR(50),
    stripe_customer_id VARCHAR(255),
    last_payment_date TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte: si premium, doit avoir une date de début
    CONSTRAINT subscription_start_required CHECK (
        (current_tier = 'free') OR 
        (current_tier != 'free' AND subscription_start IS NOT NULL)
    )
);

-- Table statistiques d'utilisation
CREATE TABLE user_usage_stats (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    letters_generated INTEGER DEFAULT 0,
    letters_generated_this_month INTEGER DEFAULT 0,
    last_generation_date TIMESTAMP WITH TIME ZONE,
    total_sessions INTEGER DEFAULT 0,
    total_session_duration INTEGER DEFAULT 0, -- en secondes
    premium_features_used INTEGER DEFAULT 0,
    favorite_tone VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table sessions utilisateurs
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Index pour performance
    CONSTRAINT sessions_expires_after_creation CHECK (expires_at > created_at)
);

-- Table métadonnées utilisateurs (stockage flexible JSON)
CREATE TABLE user_metadata (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABLES AUDIT ET SÉCURITÉ
-- =============================================================================

-- Table logs d'authentification
CREATE TABLE auth_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    action VARCHAR(50) NOT NULL CHECK (action IN ('login_success', 'login_failed', 'logout', 'password_reset', 'email_verified', 'account_locked', 'token_refresh')),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table tentatives de connexion suspectes
CREATE TABLE suspicious_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEX POUR PERFORMANCE
-- =============================================================================

-- Index utilisateurs
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_auth_provider ON users(auth_provider);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_activity ON users(last_activity);

-- Index sessions
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_is_active ON user_sessions(is_active);
CREATE INDEX idx_sessions_last_activity ON user_sessions(last_activity);

-- Index abonnements
CREATE INDEX idx_subscriptions_tier ON user_subscriptions(current_tier);
CREATE INDEX idx_subscriptions_end ON user_subscriptions(subscription_end);
CREATE INDEX idx_subscriptions_stripe ON user_subscriptions(stripe_customer_id);

-- Index profils
CREATE INDEX idx_profiles_professional_domain ON user_profiles(professional_domain);
CREATE INDEX idx_profiles_target_domain ON user_profiles(target_domain);

-- Index logs
CREATE INDEX idx_auth_logs_user_id ON auth_logs(user_id);
CREATE INDEX idx_auth_logs_action ON auth_logs(action);
CREATE INDEX idx_auth_logs_created_at ON auth_logs(created_at);
CREATE INDEX idx_auth_logs_ip ON auth_logs(ip_address);

-- Index activités suspectes
CREATE INDEX idx_suspicious_user_id ON suspicious_activities(user_id);
CREATE INDEX idx_suspicious_type ON suspicious_activities(activity_type);
CREATE INDEX idx_suspicious_ip ON suspicious_activities(ip_address);
CREATE INDEX idx_suspicious_risk ON suspicious_activities(risk_score);

-- =============================================================================
-- TRIGGERS POUR MAINTENANCE AUTOMATIQUE
-- =============================================================================

-- Fonction pour mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Application du trigger sur toutes les tables avec updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_stats_updated_at BEFORE UPDATE ON user_usage_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_metadata_updated_at BEFORE UPDATE ON user_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- FONCTIONS UTILITAIRES
-- =============================================================================

-- Fonction pour nettoyer les sessions expirées
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour nettoyer les tokens expirés
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE users 
    SET password_reset_token = NULL, 
        password_reset_expires = NULL
    WHERE password_reset_expires < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour obtenir les statistiques utilisateur
CREATE OR REPLACE FUNCTION get_user_stats()
RETURNS TABLE(
    total_users INTEGER,
    active_users INTEGER,
    premium_users INTEGER,
    users_this_month INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_users,
        COUNT(CASE WHEN status = 'active' THEN 1 END)::INTEGER as active_users,
        COUNT(CASE WHEN current_tier != 'free' THEN 1 END)::INTEGER as premium_users,
        COUNT(CASE WHEN created_at >= date_trunc('month', CURRENT_TIMESTAMP) THEN 1 END)::INTEGER as users_this_month
    FROM users u
    LEFT JOIN user_subscriptions s ON u.id = s.user_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERMISSIONS ET SÉCURITÉ
-- =============================================================================

-- Création des rôles
CREATE ROLE phoenix_app_user LOGIN;
CREATE ROLE phoenix_admin_user LOGIN;

-- Permissions pour l'application
GRANT SELECT, INSERT, UPDATE ON users TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_profiles TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_preferences TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE ON user_subscriptions TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE ON user_usage_stats TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO phoenix_app_user;
GRANT SELECT, INSERT, UPDATE ON user_metadata TO phoenix_app_user;
GRANT INSERT ON auth_logs TO phoenix_app_user;
GRANT INSERT ON suspicious_activities TO phoenix_app_user;

-- Permissions pour l'admin
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO phoenix_admin_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO phoenix_admin_user;

-- Row Level Security (RLS) pour isolation utilisateurs
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_usage_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_metadata ENABLE ROW LEVEL SECURITY;

-- Politiques RLS (à adapter selon le contexte d'authentification)
-- CREATE POLICY user_own_data ON user_profiles FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

-- =============================================================================
-- DONNÉES INITIALES
-- =============================================================================

-- Insertion d'un utilisateur admin par défaut (à modifier en production)
INSERT INTO users (email, username, password_hash, status, auth_provider, email_verified) 
VALUES ('admin@phoenix-letters.com', 'admin', '$2b$12$dummy_hash', 'active', 'email', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Profil admin
INSERT INTO user_profiles (user_id, first_name, last_name) 
SELECT id, 'Phoenix', 'Admin' FROM users WHERE email = 'admin@phoenix-letters.com'
ON CONFLICT (user_id) DO NOTHING;

-- Abonnement admin (premium)
INSERT INTO user_subscriptions (user_id, current_tier, subscription_start) 
SELECT id, 'premium_plus', CURRENT_TIMESTAMP FROM users WHERE email = 'admin@phoenix-letters.com'
ON CONFLICT (user_id) DO NOTHING;

-- =============================================================================
-- COMMENTAIRES ET DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE users IS 'Table principale des utilisateurs avec authentification et sécurité';
COMMENT ON TABLE user_profiles IS 'Profils utilisateurs avec informations personnelles';
COMMENT ON TABLE user_preferences IS 'Préférences et paramètres utilisateur';
COMMENT ON TABLE user_subscriptions IS 'Abonnements et tiers utilisateur';
COMMENT ON TABLE user_usage_stats IS 'Statistiques d''utilisation et métriques';
COMMENT ON TABLE user_sessions IS 'Sessions actives avec tokens JWT';
COMMENT ON TABLE user_metadata IS 'Stockage flexible JSON pour données additionnelles';
COMMENT ON TABLE auth_logs IS 'Logs d''authentification pour audit et sécurité';
COMMENT ON TABLE suspicious_activities IS 'Détection d''activités suspectes et fraudes';

COMMENT ON FUNCTION cleanup_expired_sessions() IS 'Nettoyage automatique des sessions expirées';
COMMENT ON FUNCTION cleanup_expired_tokens() IS 'Nettoyage des tokens de réinitialisation expirés';
COMMENT ON FUNCTION get_user_stats() IS 'Statistiques globales des utilisateurs';