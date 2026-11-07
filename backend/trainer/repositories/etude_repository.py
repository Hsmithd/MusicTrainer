import uuid
from pathlib import Path

from django.conf import settings


class EtudeRepository:
    """Stores etudes (ABC notation files) produced by the MelodyT5 model."""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or settings.MELODYT5_OUTPUT_DIR)

    def new_output_path(self):
        """A fresh file path for the model to write one generation to."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / f"etude_{uuid.uuid4().hex}.abc"

    def read(self, path):
        """Contents of a generated etude, or None if it wasn't written."""
        path = Path(path)
        return path.read_text() if path.is_file() else None
