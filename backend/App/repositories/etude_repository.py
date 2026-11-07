from pathlib import Path

from django.conf import settings


class EtudeRepository:
    """Reads etudes (ABC notation files) produced by the MelodyT5 model."""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or settings.MELODYT5_OUTPUT_DIR)

    def get_latest_abc(self):
        """Return the contents of the most recently written .abc file, or None."""
        if not self.output_dir.is_dir():
            return None
        abc_files = list(self.output_dir.glob("*.abc"))
        if not abc_files:
            return None
        latest = max(abc_files, key=lambda p: p.stat().st_mtime)
        return latest.read_text()
