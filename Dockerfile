# 🐳 Dockerfile pour Phoenix Letters - Cloud Run Ready
FROM python:3.10-slim

# Variables d'environnement optimisées pour Cloud Run
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Optimisation pour Cloud Run
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Répertoire de travail
WORKDIR /app

# Copier et installer les dépendances (pour optimiser le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port Cloud Run
EXPOSE 8080

# Healthcheck pour Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Commande de démarrage optimisée
CMD ["streamlit", "run", "app.py", \
     "--server.port", "8080", \
     "--server.address", "0.0.0.0", \
     "--server.enableCORS", "false", \
     "--server.headless", "true"]