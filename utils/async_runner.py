import asyncio
import threading
from concurrent.futures import Future
from queue import Queue
import time
import streamlit as st # Pour les messages de debug/info dans Streamlit

class AsyncServiceRunner:
    """
    Exécute des coroutines asynchrones dans un thread séparé avec sa propre boucle d'événements.
    """

    def __init__(self):
        self._loop = None
        self._thread = None
        self._is_running = False
        self._thread_ready_event = threading.Event() # Initialisation de l'événement

    def _run_loop(self):
        """Lance la boucle d'événements dans le thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._thread_ready_event.set() # Signaler que la boucle est démarrée
        # st.info("Boucle d'événements asynchrone démarrée dans un thread dédié.") # Commenté pour ne pas afficher à l'utilisateur
        self._loop.run_forever() # Exécute la boucle indéfiniment
        # st.info("Boucle d'événements asynchrone arrêtée.") # Commenté pour ne pas afficher à l'utilisateur

    def start(self):
        """Démarre le thread et sa boucle d'événements."""
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self._thread_ready_event.wait(timeout=5) # Attendre que le thread soit prêt
            if not self._thread_ready_event.is_set():
                st.error("Le thread asynchrone n'a pas démarré à temps.")
                raise RuntimeError("Le thread asynchrone n'a pas démarré à temps.")
            # st.success("Service asynchrone démarré dans un thread dédié.") # Commenté pour ne pas afficher à l'utilisateur

    def stop(self):
        """Arrête le thread et sa boucle d'événements."""
        if self._is_running and self._loop:
            self._is_running = False
            # Arrêter la boucle d'événements de manière thread-safe
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=1) # Attendre la fin du thread
            if self._thread.is_alive():
                st.warning("Le thread asynchrone n'a pas pu s'arrêter proprement.")
            self._loop = None
            self._thread = None
            # st.info("Service asynchrone arrêté.") # Commenté pour ne pas afficher à l'utilisateur

    def run_coro_in_thread(self, coro):
        """Exécute une coroutine dans le thread asynchrone et retourne une Future."""
        if not self._is_running or not self._loop:
            raise RuntimeError("Le service asynchrone n'est pas démarré.")
        
        # Soumettre la coroutine à la boucle d'événements du thread de manière thread-safe
        # et retourner une Future qui sera résolue dans le thread appelant
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
