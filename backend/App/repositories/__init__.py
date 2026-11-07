"""Data-access layer.

Repositories are the only code that knows *where* data lives (database
tables, files on disk, ...). Services call repositories; views never do.
"""
from .etude_repository import EtudeRepository
from .user_repository import UserRepository

__all__ = ["EtudeRepository", "UserRepository"]
