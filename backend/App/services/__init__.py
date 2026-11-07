"""Business-logic layer.

Services hold the application's rules and orchestration. They are called
by views (the HTTP layer) and use repositories for data access.
"""
from .auth_service import AuthService
from .etude_service import EtudeGenerationError, EtudeService

__all__ = ["AuthService", "EtudeService", "EtudeGenerationError"]
