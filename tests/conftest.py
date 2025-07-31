import pytest
from dotenv import load_dotenv
import os

@pytest.fixture(scope='session', autouse=True)
def load_env():
    # Charge les variables d'environnement du fichier .env
    # Assurez-vous que le fichier .env est à la racine du projet ou spécifiez le chemin
    # Construire le chemin absolu vers le fichier .env
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path=dotenv_path)
    # Vérifie si GOOGLE_API_KEY est chargée
    if not os.getenv('GOOGLE_API_KEY'):
        pytest.fail(f"GOOGLE_API_KEY not found in .env file at {dotenv_path}. Please set it for integration tests.")

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
